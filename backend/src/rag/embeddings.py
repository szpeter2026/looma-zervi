"""
Embedding generation utilities.
Uses DeepSeek or a local model for text embeddings.
"""
# TODO: migrate embedding logic from DemoPeter
# Options:
# 1. DeepSeek embedding API (if available)
# 2. Local sentence-transformers model
# 3. Ollama nomic-embed-text (fallback)


def generate_embedding(text: str) -> list:
    """Generate an embedding vector for the given text."""
    # TODO: implement based on available model
    raise NotImplementedError("Embedding generation not yet migrated")
