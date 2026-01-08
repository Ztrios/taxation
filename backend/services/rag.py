from google import genai
import weaviate
from weaviate.auth import AuthApiKey
from config import settings
from typing import List, Tuple

# Initialize Weaviate client
def get_client() -> weaviate.WeaviateClient:
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=settings.weaviate_url,
        auth_credentials=AuthApiKey(settings.weaviate_api_key),
        headers={"X-OpenAI-Project": "legal-rag"}
    )

# Embed a query string using Gemini Embedding
def embed_query(query: str) -> List[float]:
    """Embed a query string using Gemini."""
    client = genai.Client(api_key=settings.gemini_api_key)
    # Note: dimensions parameter is not supported in this version of google-genai
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=query,
    )
    # google-genai EmbedContentResponse has embeddings attribute (list)
    # Each embedding has a values attribute (list of floats)
    if hasattr(response, "embeddings") and len(response.embeddings) > 0:
        embedding = response.embeddings[0]
        if hasattr(embedding, "values"):
            vector = embedding.values
        elif isinstance(embedding, list):
            vector = embedding
        else:
            raise RuntimeError(f"Unexpected embedding format: {type(embedding)}")
    elif hasattr(response, "embedding"):
        # Fallback for singular embedding attribute
        vector = response.embedding
    else:
        raise RuntimeError(f"Unexpected response format: {type(response)}, attributes: {dir(response)}")
    
    # Log dimension (query vectors should match ingestion vectors)
    if len(vector) != settings.expected_embedding_dim:
        import logging
        logging.warning(
            f"Query embedding dimension: {len(vector)} (expected {settings.expected_embedding_dim}). "
            f"This should match the ingestion dimension."
        )
    return vector

# Retrieve documents similar to query
def retrieve(
    client: weaviate.WeaviateClient, query: str, top_k: int = 4, alpha: float = 0.5
) -> List[Tuple[str, str, int, float]]:
    """Hybrid search returning (content, filename, chunk_index, score)."""
    collection = client.collections.get(settings.collection_name)
    query_vector = embed_query(query)
    result = collection.query.hybrid(
        query=query,
        vector=query_vector,
        alpha=alpha,
        limit=top_k,
        return_metadata=weaviate.classes.query.MetadataQuery(distance=True, score=True),
    )
    hits: List[Tuple[str, str, int, float]] = []
    for o in result.objects:
        props = o.properties
        score = o.metadata.score if hasattr(o.metadata, "score") else None
        hits.append(
            (
                props.get("content", ""),
                props.get("filename", ""),
                props.get("chunk_index", -1),
                score if score is not None else 0.0,
            )
        )

    context_blocks = []
    for idx, (content, filename, chunk_idx, score) in enumerate(hits, 1):
        context_blocks.append(
            f"[Context {idx}] Source: {filename} (Chunk {chunk_idx}, Relevance Score: {score:.4f})\n{content}"
        )
    context_text = "\n\n" + "="*80 + "\n\n".join(context_blocks) + "\n\n" + "="*80
    
    return context_text


if __name__ == "__main__":
    client = get_client()
    try:
        query = "Can I deduct the municipal taxes or local rates I pay for my business premises?"
        context = retrieve(client, query)
        print(context)
    finally:
        client.close()