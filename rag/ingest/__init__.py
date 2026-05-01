import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".html"}

class DocumentIngestor:
    def __init__(self, docs_dir: Optional[Path] = None):
        self.docs_dir = docs_dir or Path(__file__).parent.parent.parent / "docs"
        self.docs_dir.mkdir(exist_ok=True)
    
    def ingest_file(self, file_path: Path) -> Optional[Dict]:
        ext = file_path.suffix.lower()
        
        if ext == ".pdf":
            return self._ingest_pdf(file_path)
        elif ext in {".txt", ".md", ".markdown"}:
            return self._ingest_text(file_path)
        elif ext == ".html":
            return self._ingest_html(file_path)
        return None
    
    def _ingest_pdf(self, path: Path) -> Optional[Dict]:
        try:
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.Preader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
            
            if not text.strip():
                return None
                
            return {
                "source": str(path),
                "filename": path.name,
                "type": "pdf",
                "content": text,
                "chunks": self._chunk_text(text, path.name)
            }
        except ImportError:
            print("PyPDF2 not installed. Run: pip install PyPDF2")
            return None
        except Exception as e:
            print(f"Error reading PDF {path}: {e}")
            return None
    
    def _ingest_text(self, path: Path) -> Optional[Dict]:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return {
                "source": str(path),
                "filename": path.name,
                "type": "text",
                "content": content,
                "chunks": self._chunk_text(content, path.name)
            }
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return None
    
    def _ingest_html(self, path: Path) -> Optional[Dict]:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            text = soup.get_text(separator="\n")
            return {
                "source": str(path),
                "filename": path.name,
                "type": "html",
                "content": text,
                "chunks": self._chunk_text(text, path.name)
            }
        except ImportError:
            return self._ingest_text(path)
        except Exception as e:
            print(f"Error reading HTML {path}: {e}")
            return None
    
    def _chunk_text(self, text: str, source: str, chunk_size: int = 1000) -> List[Dict]:
        sentences = text.replace("\n", " ").split(". ")
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "source": source,
                        "char_count": len(current_chunk)
                    })
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "source": source,
                "char_count": len(current_chunk)
            })
        
        return chunks
    
    def ingest_directory(self, directory: Optional[Path] = None) -> List[Dict]:
        docs = []
        dir_path = directory or self.docs_dir
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                path = Path(root) / file
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    doc = self.ingest_file(path)
                    if doc:
                        docs.append(doc)
        
        return docs
    
    def add_document(self, source: str) -> Dict:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        
        doc = self.ingest_file(path)
        if not doc:
            raise ValueError(f"Failed to ingest: {source}")
        
        dest = self.docs_dir / path.name
        import shutil
        shutil.copy(path, dest)
        
        return doc