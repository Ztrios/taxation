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


# Singleton instance
storage = RedisStorage()
