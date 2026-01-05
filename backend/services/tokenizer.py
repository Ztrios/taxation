from typing import List, Dict


def count_tokens(text: str) -> int:
    """
    Count tokens using Hugging Face AutoTokenizer.
    
    This function is left as a placeholder for you to implement
    with the exact model tokenizer.
    
    Args:
        text: The text to count tokens for
        
    Returns:
        int: Number of tokens in the text
    """
    # TODO: Implement using transformers.AutoTokenizer
    # Example implementation:
    # from transformers import AutoTokenizer
    # from config import settings
    # tokenizer = AutoTokenizer.from_pretrained(settings.model_hf_path)
    # return len(tokenizer.encode(text))
    
    # Temporary approximation (remove when implementing)
    return len(text.split()) * 2


def count_messages_tokens(messages: List[Dict[str, str]]) -> int:
    """
    Count total tokens in a list of messages.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        
    Returns:
        int: Total number of tokens
    """
    total = 0
    for message in messages:
        # Count tokens for role and content
        total += count_tokens(f"{message['role']}: {message['content']}")
    return total
