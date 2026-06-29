"""
ChromaDB vector store client.
Handles knowledge base embedding storage and similarity search.
"""
import chromadb
from flask import current_app


def get_chroma_client():
    """Get or create a ChromaDB client based on config (local or remote)."""
    config = current_app.config
    mode = config["CHROMA_MODE"]

    if mode == "remote":
        client = chromadb.HttpClient(
            host=config["CHROMA_HOST"],
            port=int(config["CHROMA_PORT"]),
        )
    else:
        # local persistent mode
        client = chromadb.PersistentClient(path="chroma_data")

    return client


def get_or_create_collection():
    """Get or create the main knowledge base collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=current_app.config["CHROMA_COLLECTION"],
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(documents: list, metadatas: list = None, ids: list = None):
    """Add documents to the vector store."""
    collection = get_or_create_collection()
    if ids is None:
        ids = [f"doc_{i}" for i in range(len(documents))]
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )


def search(query: str, n_results: int = 5):
    """
    Search the knowledge base for relevant chunks.
    Returns list of {document, metadata, distance} dicts.
    """
    collection = get_or_create_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {"document": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]
