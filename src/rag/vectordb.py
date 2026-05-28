"""
VectorDB - Stores and retrieves news embeddings using LangChain + ChromaDB
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import VECTORDB_PATH


# Lazy — loaded on first use, not at import time.
# Module-level instantiation caused uvicorn --reload to crash because
# HuggingFaceEmbeddings tries to reach huggingface.co at import time,
# and the subprocess HTTP client gets closed before the request completes.
_embeddings = None

# Chunk size ~500 chars (~380 tokens) fits well under the 512-token limit of
# all-MiniLM-L6-v2. Overlap of 100 chars carries one sentence of context
# across chunk boundaries so no fact falls in a gap.
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def get_vectorstore() -> Chroma:
    """Return a persistent Chroma vectorstore instance."""
    os.makedirs(VECTORDB_PATH, exist_ok=True)
    return Chroma(
        collection_name="cricket_news",
        embedding_function=_get_embeddings(),
        persist_directory=VECTORDB_PATH,
    )


def add_documents(news_items: list[dict]) -> int:
    """
    Add news items to the vector store.
    Full article content is split into overlapping chunks before embedding
    so no part of the story is lost due to the model's 512-token limit.

    Args:
        news_items: List of dicts with 'headline', 'content', 'source', 'sentiment'

    Returns:
        Number of chunks added
    """
    if not news_items:
        return 0

    all_chunks = []
    for item in news_items:
        content = item.get("content", item["headline"])
        metadata = {
            "headline": item["headline"][:200],
            "source": item.get("source", "unknown"),
            "sentiment": item.get("sentiment", "neutral"),
        }

        # Split into chunks — each chunk gets the same metadata so retrieval
        # results always carry headline + source regardless of which chunk matched.
        chunks = _splitter.create_documents([content], metadatas=[metadata])
        all_chunks.extend(chunks)

    vectorstore = get_vectorstore()
    vectorstore.add_documents(all_chunks)
    return len(all_chunks)


def search(query: str, n_results: int = 5) -> list[dict]:
    """
    Search for relevant documents.

    Args:
        query: Search query string
        n_results: Number of results to return

    Returns:
        List of dicts with 'content', 'headline', 'source', 'relevance'
    """
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_relevance_scores(query, k=n_results)

    return [
        {
            "content": doc.page_content,
            "headline": doc.metadata.get("headline", ""),
            "source": doc.metadata.get("source", "unknown"),
            "relevance": round(score, 2),
        }
        for doc, score in results
    ]


def get_retriever(n_results: int = 5):
    """Return a LangChain retriever for use in RAG chains."""
    return get_vectorstore().as_retriever(search_kwargs={"k": n_results})


def get_count() -> int:
    """Get total number of documents in the collection."""
    try:
        return get_vectorstore()._collection.count()
    except Exception:
        return 0


def clear() -> bool:
    """Clear all documents from the collection."""
    try:
        store = get_vectorstore()
        store.delete_collection()
        return True
    except Exception as e:
        print(f"⚠️ VectorDB clear error: {e}")
        return False