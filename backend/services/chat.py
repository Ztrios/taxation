from typing import List, Dict, Optional
from openai import OpenAI
import weaviate
from config import settings
from services.storage import storage
from services.tokenizer import count_messages_tokens


class ChatService:
    def __init__(self):
        # Initialize OpenAI client (compatible with vLLM)
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        
        # Initialize Weaviate client
        self.weaviate_client = weaviate.Client(
            url=settings.weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=settings.weaviate_api_key)
        )
    
    def truncate_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Truncate message history from the beginning if token count exceeds limit.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List[Dict[str, str]]: Truncated messages
        """
        while len(messages) > 1:  # Keep at least one message
            token_count = count_messages_tokens(messages)
            if token_count <= settings.max_tokens:
                break
            # Remove oldest message (from beginning)
            messages.pop(0)
        
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
        
        # Add user message to history
        history.append({"role": "user", "content": user_message})
        
        # Truncate if exceeds token limit
        history = self.truncate_history(history)
        
        # Prepare messages for LLM
        messages = history.copy()
        
        # Add RAG context if enabled
        if include_rag:
            rag_context = self.get_rag_context(user_message)
            if rag_context:
                # Insert context before the last user message
                context_message = {
                    "role": "system",
                    "content": f"Relevant context:\n{rag_context}"
                }
                messages.insert(-1, context_message)
        
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
            
            return assistant_message
        except Exception as e:
            error_msg = f"Error calling LLM: {str(e)}"
            print(error_msg)
            return error_msg


# Singleton instance
chat_service = ChatService()
