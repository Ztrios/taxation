from typing import List, Dict, Optional
from openai import OpenAI
import weaviate
from config import settings
from services.storage import storage
from services.tokenizer import count_messages_tokens
from services.query_rewriter import query_rewriter


class ChatService:
    def __init__(self):
        # Initialize OpenAI client (compatible with vLLM)
        # OpenRouter supports OpenAI-compatible API, but recommends extra headers.
        # These are optional and safe for other OpenAI-compatible providers.
        default_headers = {
            "HTTP-Referer": "http://localhost",  # OpenRouter: identifies your app (can be changed)
            "X-Title": "taxation-chatbot",       # OpenRouter: identifies your app (can be changed)
        }
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            default_headers=default_headers,
        )

        # Model fallback chain: if the selected model has no available endpoints,
        # we'll try a couple of common alternatives so the app stays usable.
        self.model_candidates = [
            settings.model_name,
            # Widely available Qwen instruct model (good for chat)
            "qwen/qwen-2.5-7b-instruct",
            # A very common free model, as last resort
            "qwen/qwen3-4b:free",
        ]

        # Initialize Weaviate client (v4). Keep optional so the API can run even if Weaviate is down.
        self.weaviate_client: Optional[weaviate.WeaviateClient] = None
        try:
            # Add Cohere API key to headers for vectorization
            additional_headers = {}
            if settings.cohere_apikey:
                additional_headers["X-Cohere-Api-Key"] = settings.cohere_apikey
            
            # ✅ Use v4 syntax: connect_to_weaviate_cloud (not deprecated connect_to_wcs)
            self.weaviate_client = weaviate.connect_to_weaviate_cloud(
                cluster_url=f"https://{settings.weaviate_url}",  # Ensure https:// prefix
                auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
                headers=additional_headers if additional_headers else None,
            )
            print("✅ Weaviate connected with Cohere API key (v4)")
        except Exception as e:
            print(f"Weaviate init error (RAG disabled): {e}")
    
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
    
    def get_rag_context(self, query: str, limit: int = 3, use_rewriter: bool = True) -> str:
        """
        Retrieve relevant context from Weaviate RAG with optional query rewriting.
        
        Args:
            query: User query
            limit: Number of results to retrieve per rewritten query
            use_rewriter: Whether to use query rewriting for better results
            
        Returns:
            str: Concatenated context
        """
        if self.weaviate_client is None:
            return ""

        # Step 1: Rewrite query into better search terms (if enabled)
        queries_to_search = [query]  # Default: use original
        if use_rewriter:
            try:
                rewritten = query_rewriter.rewrite(query)
                if rewritten:
                    queries_to_search = rewritten
                    print(f"Query rewriter: '{query}' → {rewritten}")
            except Exception as e:
                print(f"Query rewriter failed, using original: {e}")

        # Step 2: Search Weaviate with all rewritten queries
        all_contexts: List[str] = []
        seen_content = set()  # Deduplicate results

        for search_query in queries_to_search:
            try:
                collection = self.weaviate_client.collections.get("Document")
                response = collection.query.near_text(
                    query=search_query,
                    limit=limit,
                    return_properties=["content", "metadata"],
                )

                for obj in getattr(response, "objects", []) or []:
                    props = getattr(obj, "properties", {}) or {}
                    content = props.get("content", "")
                    if content and content not in seen_content:
                        all_contexts.append(content)
                        seen_content.add(content)
            except Exception as e:
                print(f"RAG retrieval error for '{search_query}': {e}")
                continue

        return "\n\n".join(all_contexts) if all_contexts else ""
    
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
            # Always add system message with strict instruction
            context_message = {
                "role": "system",
                "content": f"You are strictly bound to reply based on the relevant context. If relevant context is empty, say that you're sorry and you cannot answer this question.\nRelevant context:\n{rag_context if rag_context else '[No relevant context found]'}"
            }
            messages.insert(-1, context_message)
        
        # Call LLM
        last_error: Optional[Exception] = None

        for model in self.model_candidates:
            try:
                response = self.llm_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                )

                assistant_message = response.choices[0].message.content

                # Add assistant response to history
                history.append({"role": "assistant", "content": assistant_message})

                # Save updated history
                storage.save_history(session_id, history)

                return assistant_message
            except Exception as e:
                # Continue to next model only for the common OpenRouter case:
                # "No endpoints found for <model>".
                msg = str(e)
                last_error = e
                if "No endpoints found for" in msg:
                    continue
                raise RuntimeError(f"Error calling LLM: {msg}") from e

        raise RuntimeError(f"Error calling LLM: {str(last_error)}") from last_error


# Singleton instance
chat_service = ChatService()
