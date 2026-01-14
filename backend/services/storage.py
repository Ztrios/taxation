import redis
import json
from typing import List, Dict
from config import settings


class RedisStorage:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve chat history for a session."""
        history_json = self.client.get(f"chat:{session_id}")
        if history_json:
            return json.loads(history_json)
        return []
    
    def save_history(self, session_id: str, history: List[Dict[str, str]]) -> None:
        """Save chat history for a session."""
        self.client.set(f"chat:{session_id}", json.dumps(history))
    
    def append_message(self, session_id: str, role: str, content: str) -> None:
        """Append a single message to the history."""
        history = self.get_history(session_id)
        history.append({"role": role, "content": content})
        self.save_history(session_id, history)
    
    def clear_history(self, session_id: str) -> None:
        """Clear chat history for a session."""
        self.client.delete(f"chat:{session_id}")
        # Also delete metadata
        self.client.delete(f"chat_meta:{session_id}")
    
    def get_all_sessions(self) -> List[Dict[str, str]]:
        """Get all chat sessions with metadata."""
        sessions = []
        # Get all chat session keys
        keys = self.client.keys("chat:*")
        
        for key in keys:
            session_id = key.replace("chat:", "")
            # Skip metadata keys
            if session_id.startswith("meta:"):
                continue
                
            history = self.get_history(session_id)
            if history:
                # Get first user message as preview
                first_message = next((msg for msg in history if msg.get("role") == "user"), None)
                preview = first_message.get("content", "New Chat")[:50] if first_message else "New Chat"
                
                # Get or create metadata
                meta_key = f"chat_meta:{session_id}"
                meta_json = self.client.get(meta_key)
                
                if meta_json:
                    metadata = json.loads(meta_json)
                else:
                    # Create metadata if it doesn't exist
                    import time
                    metadata = {
                        "created_at": int(time.time()),
                        "updated_at": int(time.time())
                    }
                    self.client.set(meta_key, json.dumps(metadata))
                
                sessions.append({
                    "session_id": session_id,
                    "preview": preview,
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at")
                })
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return sessions
    
    def update_session_timestamp(self, session_id: str) -> None:
        """Update the last updated timestamp for a session."""
        import time
        meta_key = f"chat_meta:{session_id}"
        meta_json = self.client.get(meta_key)
        
        if meta_json:
            metadata = json.loads(meta_json)
            metadata["updated_at"] = int(time.time())
        else:
            metadata = {
                "created_at": int(time.time()),
                "updated_at": int(time.time())
            }
        
        self.client.set(meta_key, json.dumps(metadata))
    
    def add_pending_document(self, session_id: str, filename: str, file_path: str, extracted_text: str) -> None:
        """Add a document to the pending list for this session."""
        pending_key = f"pending_docs:{session_id}"
        pending_docs = self.get_pending_documents(session_id)
        
        pending_docs.append({
            "filename": filename,
            "file_path": file_path,
            "extracted_text": extracted_text
        })
        
        self.client.set(pending_key, json.dumps(pending_docs))
    
    def get_pending_documents(self, session_id: str) -> List[Dict[str, str]]:
        """Get all pending documents for this session."""
        pending_key = f"pending_docs:{session_id}"
        pending_json = self.client.get(pending_key)
        if pending_json:
            return json.loads(pending_json)
        return []
    
    def clear_pending_documents(self, session_id: str) -> None:
        """Clear all pending documents for this session."""
        pending_key = f"pending_docs:{session_id}"
        self.client.delete(pending_key)


# Singleton instance
storage = RedisStorage()
