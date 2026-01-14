from typing import List, Dict, Optional
from openai import OpenAI
import weaviate
from config import settings
from services.storage import storage
from services.tokenizer import count_messages_tokens
from services.rag import get_context


class ChatService:
    def __init__(self):
        # Initialize OpenAI client (compatible with vLLM)
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        
        # # Initialize Weaviate client
        # self.weaviate_client = weaviate.Client(
        #     url=settings.weaviate_url,
        #     auth_client_secret=weaviate.AuthApiKey(api_key=settings.weaviate_api_key)
        # )
    
    def truncate_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Truncate message history if token count exceeds limit.
        Always protects the first message (system prompt).
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List[Dict[str, str]]: Truncated messages
        """
        while len(messages) > 2:  # Keep at least system prompt + one other message
            token_count = count_messages_tokens(messages)
            if token_count <= settings.max_tokens:
                break
            # Remove second message (first after system prompt)
            messages.pop(1)
        
        return messages
    
    def get_rag_context(self, query: str, limit: int = 3) -> str:
        """
        Retrieve relevant context from Weaviate RAG.
        
        Args:
            query: User query
            limit: Number of results to retrieve
            
        Returns:
            str: Concatenated context
        """
        try:
            # Query Weaviate (adjust class name and properties as needed)
            result = (
                self.weaviate_client.query
                .get("Document", ["content", "metadata"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            # Extract and concatenate context
            contexts = []
            if "data" in result and "Get" in result["data"]:
                documents = result["data"]["Get"].get("Document", [])
                for doc in documents:
                    contexts.append(doc.get("content", ""))
            
            return "\n\n".join(contexts)
        except Exception as e:
            print(f"RAG retrieval error: {e}")
            return ""
    
    def _initialize_system_prompt(self) -> Dict[str, str]:
        """
        Create the initial system prompt with empty knowledge base.
        
        Returns:
            Dict[str, str]: System message dictionary
        """
        return {
            "role": "system",
            "content": "You are strictly bound to reply based on the relevant context. If relevant context is empty, say that you're sorry and you cannot answer this question.\n\n<knowledge_base>\n</knowledge_base>"
        }
    
    def _extract_context_identifiers(self, context_text: str) -> set:
        """
        Extract unique identifiers from context blocks.
        Each context block has format: [Context N] Source: filename (Chunk chunk_idx, ...)
        
        Args:
            context_text: Context text containing multiple context blocks
            
        Returns:
            set: Set of tuples (filename, chunk_idx) representing unique contexts
        """
        import re
        identifiers = set()
        
        # Pattern to match: Source: filename (Chunk chunk_idx, ...
        pattern = r'Source:\s+([^\(]+)\s+\(Chunk\s+(\d+)'
        matches = re.findall(pattern, context_text)
        
        for filename, chunk_idx in matches:
            identifiers.add((filename.strip(), int(chunk_idx)))
        
        return identifiers
    
    def _update_knowledge_base(self, system_content: str, new_context: str) -> str:
        """
        Append new RAG context to the knowledge base in system prompt.
        Deduplicates contexts based on filename and chunk_index.
        
        Args:
            system_content: Current system message content
            new_context: New context to append
            
        Returns:
            str: Updated system content with appended context
        """
        # Find the knowledge_base tags
        kb_start = system_content.find("<knowledge_base>")
        kb_end = system_content.find("</knowledge_base>")
        
        if kb_start == -1 or kb_end == -1:
            # If tags don't exist, add them with the new context
            return system_content + f"\n\n<knowledge_base>\n{new_context}\n</knowledge_base>"
        
        # Extract current knowledge base content
        kb_content = system_content[kb_start + len("<knowledge_base>"):kb_end].strip()
        
        # Get existing context identifiers
        existing_identifiers = self._extract_context_identifiers(kb_content)
        
        # Parse new context blocks and filter out duplicates
        import re
        new_context_blocks = []
        
        # Split new context into individual blocks
        # Context blocks are separated by "=" * 80
        context_parts = new_context.split("=" * 80)
        
        for part in context_parts:
            part = part.strip()
            if not part:
                continue
            
            # Extract identifier from this context block
            pattern = r'Source:\s+([^\(]+)\s+\(Chunk\s+(\d+)'
            match = re.search(pattern, part)
            
            if match:
                filename = match.group(1).strip()
                chunk_idx = int(match.group(2))
                identifier = (filename, chunk_idx)
                
                # Only add if not already in knowledge base
                if identifier not in existing_identifiers:
                    new_context_blocks.append(part)
                    existing_identifiers.add(identifier)
        
        # If no new contexts to add, return unchanged
        if not new_context_blocks:
            return system_content
        
        # Append new unique contexts
        new_contexts_text = "\n\n" + ("=" * 80 + "\n\n").join(new_context_blocks)
        
        if kb_content:
            updated_kb = kb_content + new_contexts_text
        else:
            updated_kb = new_contexts_text.strip()
        
        # Reconstruct the system content
        before_kb = system_content[:kb_start]
        after_kb = system_content[kb_end + len("</knowledge_base>"):]
        
        return f"{before_kb}<knowledge_base>\n{updated_kb}\n</knowledge_base>{after_kb}"
    
    def chat(
        self,
        session_id: str,
        user_message: str,
        include_rag: bool = True
    ) -> str:
        """
        Process a chat message with history management and RAG.
        
        Args:
            session_id: Unique session identifier
            user_message: User's message
            include_rag: Whether to include RAG context
            
        Returns:
            str: Assistant's response
        """
        # Get history from Redis
        history = storage.get_history(session_id)
        
        # Initialize with system prompt if this is a new session
        if not history:
            history.append(self._initialize_system_prompt())
        
        # Add user message to history
        history.append({"role": "user", "content": user_message})
        
        # Prepare messages for LLM
        messages = history.copy()
        
        # Add RAG context if enabled
        if include_rag:
            rag_context = get_context(user_message)
            if rag_context:
                # Update the system prompt's knowledge base
                messages[0]["content"] = self._update_knowledge_base(
                    messages[0]["content"],
                    rag_context
                )

        # Truncate if exceeds token limit (protects system prompt)
        messages = self.truncate_history(messages)
        
        # Call LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            assistant_message = response.choices[0].message.content
            
            # Add assistant response to history
            history.append({"role": "assistant", "content": assistant_message})
            
            # Save updated history
            storage.save_history(session_id, history)
            
            # Update session timestamp
            storage.update_session_timestamp(session_id)
            
            return assistant_message
        except Exception as e:
            error_msg = f"Error calling LLM: {str(e)}"
            print(error_msg)
            return error_msg


# Singleton instance
chat_service = ChatService()
