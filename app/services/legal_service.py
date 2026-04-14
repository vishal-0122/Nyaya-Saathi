from app.db.chroma.client import get_collection
from app.core.rag.embedding import embed_text
import logging

logger = logging.getLogger(__name__)

def retrieve_legal_docs(query: str):
    try:
        collection = get_collection()
        query_embedding = embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        docs = []
        for i in range(len(results["documents"][0])):
            docs.append({
                "description": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            })

        return docs
    except Exception:
        logger.exception("Legal retrieval failed")
        return []