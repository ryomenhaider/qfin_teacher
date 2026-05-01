from typing import List, Dict, Optional
import numpy as np

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384
    
    def load_model(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
            except ImportError:
                print("sentence-transformers not installed. Run: pip install sentence-transformers")
                raise
            except Exception as e:
                print(f"Error loading model: {e}")
                raise
    
    def encode(self, texts: List[str]) -> np.ndarray:
        if self.model is None:
            self.load_model()
        
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return np.array(embeddings)
    
    def encode_chunk(self, chunk: Dict) -> np.ndarray:
        return self.encode([chunk["text"]])[0]
    
    def encode_chunks(self, chunks: List[Dict]) -> np.ndarray:
        texts = [c["text"] for c in chunks]
        return self.encode(texts)

class FallbackEmbedder:
    def __init__(self):
        self.embedding_dim = 384
    
    def encode(self, texts: List[str]) -> np.ndarray:
        np.random.seed(42)
        return np.random.randn(len(texts), self.embedding_dim).astype(np.float32)
    
    def encode_chunk(self, chunk: Dict) -> np.ndarray:
        return self.encode([chunk["text"]])[0]
    
    def encode_chunks(self, chunks: List[Dict]) -> np.ndarray:
        return self.encode([c["text"] for c in chunks])

def get_embedder() -> Embedder:
    try:
        return Embedder()
    except:
        return FallbackEmbedder()