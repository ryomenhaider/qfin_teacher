from typing import List, Dict, Optional, Tuple
import numpy as np
from ..embed import get_embedder
from ..store import VectorStore

class Retriever:
    def __init__(self, vector_store: Optional[VectorStore] = None, embedder = None):
        self.vector_store = vector_store or VectorStore()
        self.embedder = embedder or get_embedder()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.embedder.encode([query])[0]
        results = self.vector_store.search(query_embedding, k=top_k)
        
        formatted_results = []
        for chunk, distance in results:
            formatted_results.append({
                "text": chunk["text"],
                "source": chunk.get("source", "unknown"),
                "score": 1 / (1 + distance)
            })
        
        return formatted_results
    
    def rag_answer(self, query: str, top_k: int = 5) -> Tuple[str, List[Dict]]:
        context_chunks = self.retrieve(query, top_k)
        
        if not context_chunks:
            return "No relevant documents found. Add documents first.", []
        
        context = "\n\n".join([
            f"[Source: {c['source']}]\n{c['text'][:500]}"
            for c in context_chunks
        ])
        
        return context, context_chunks

class TutorRetriever(Retriever):
    def __init__(self, vector_store: Optional[VectorStore] = None):
        super().__init__(vector_store)
    
    def build_context_for_tutor(self, query: str) -> Dict:
        context, chunks = self.rag_answer(query, top_k=5)
        
        return {
            "query": query,
            "context": context,
            "sources": list(set(c["source"] for c in chunks)),
            "chunks": chunks
        }