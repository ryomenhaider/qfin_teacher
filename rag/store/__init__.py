from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import json
import pickle

DATA_DIR = Path(__file__).parent.parent.parent / "data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
CHUNKS_FILE = VECTOR_STORE_DIR / "chunks.json"
INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
META_FILE = VECTOR_STORE_DIR / "meta.pkl"

class VectorStore:
    def __init__(self, embedder_dim: int = 384):
        self.embedder_dim = embedder_dim
        self.index = None
        self.chunks = []
        self.doc_sources = {}
    
    def _init_index(self):
        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.embedder_dim)
            self.faiss = faiss
        except ImportError:
            print("faiss not installed. Run: pip install faiss-cpu")
            raise
    
    def add_chunks(self, chunks: List[Dict], embeddings: np.ndarray):
        if self.index is None:
            self._init_index()
        
        if embeddings.shape[1] != self.embedder_dim:
            raise ValueError(f"Embedding dimension mismatch: {embeddings.shape[1]} != {self.embedder_dim}")
        
        embeddings = embeddings.astype(np.float32)
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        
        for chunk in chunks:
            source = chunk.get("source", "unknown")
            if source not in self.doc_sources:
                self.doc_sources[source] = []
            self.doc_sources[source].append(len(self.chunks) - 1)
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[Dict, float]]:
        if self.index is None:
            return []
        
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        try:
            distances, indices = self.index.search(query_embedding, k)
        except:
            return []
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.chunks):
                results.append((self.chunks[idx], float(dist)))
        
        return results
    
    def save(self):
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        
        if self.index is not None:
            try:
                import faiss
                faiss.write_index(self.index, str(INDEX_FILE))
            except:
                pass
        
        with open(CHUNKS_FILE, "w") as f:
            json.dump(self.chunks, f, indent=2)
        
        with open(META_FILE, "wb") as f:
            pickle.dump(self.doc_sources, f)
    
    def load(self) -> bool:
        if not CHUNKS_FILE.exists():
            return False
        
        try:
            with open(CHUNKS_FILE, "r") as f:
                self.chunks = json.load(f)
            
            if INDEX_FILE.exists():
                try:
                    import faiss
                    self.index = faiss.read_index(str(INDEX_FILE))
                    self.embedder_dim = self.index.d
                except:
                    self._init_index()
            else:
                self._init_index()
            
            if META_FILE.exists():
                with open(META_FILE, "rb") as f:
                    self.doc_sources = pickle.load(f)
            
            return True
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return False
    
    def clear(self):
        self.index = None
        self.chunks = []
        self.doc_sources = {}
        
        for f in [CHUNKS_FILE, INDEX_FILE, META_FILE]:
            if f.exists():
                f.unlink()
    
    def get_stats(self) -> Dict:
        return {
            "total_chunks": len(self.chunks),
            "unique_sources": len(self.doc_sources),
            "sources": list(self.doc_sources.keys())
        }