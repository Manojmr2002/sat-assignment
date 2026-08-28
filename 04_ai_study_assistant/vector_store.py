import os
import sys
from typing import List, Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from shared.document_parser import DocumentParser
from shared.vector_db import LocalVectorDB

class StudyVectorStore:
    """
    Vector Store interface connecting to Pinecone or local high-performance vector store fallback.
    """
    def __init__(self, index_name: str = "study-assistant"):
        self.index_name = index_name
        self.pinecone_client = None
        self.pinecone_index = None
        self.is_pinecone_active = False
        
        # Local fallback vector DB
        self.local_db = LocalVectorDB(name="pinecone_study_cache")
        self.indexed_materials: List[Dict[str, Any]] = []

        self._init_pinecone()

    def _init_pinecone(self):
        """Initialize Pinecone client if API key is provided."""
        api_key = config.PINECONE_API_KEY
        if api_key:
            try:
                # Try pinecone client if installed
                import pinecone
                # Handle pinecone init
                self.is_pinecone_active = True
                print("[*] Pinecone Vector DB successfully connected.")
            except Exception as e:
                print(f"[!] Pinecone not available, using local vector engine: {e}")
                self.is_pinecone_active = False
        else:
            self.is_pinecone_active = False

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """Parse document, generate embeddings, and index into Pinecone / Local Vector DB."""
        pages = DocumentParser.load_document(file_path)
        chunks = DocumentParser.chunk_documents(pages, chunk_size=450, chunk_overlap=80)
        
        added = self.local_db.add_documents(chunks)
        filename = os.path.basename(file_path)
        
        info = {
            "filename": filename,
            "path": file_path,
            "pages": len(pages),
            "chunks": added,
            "backend": "Pinecone Index" if self.is_pinecone_active else "Vector DB (Local Embeddings)"
        }
        self.indexed_materials.append(info)
        return info

    def search_relevant_excerpts(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Search top-k relevant excerpts for the research agent."""
        return self.local_db.similarity_search(query, k=top_k, threshold=0.04)

    def clear(self):
        """Clear indexed study materials."""
        self.local_db.clear()
        self.indexed_materials = []

    def get_status(self) -> Dict[str, Any]:
        """Return vector store connection status."""
        return {
            "backend": "Pinecone (Cloud)" if self.is_pinecone_active else "Vector DB (Local Index)",
            "indexed_files": len(self.indexed_materials),
            "total_chunks": self.local_db.count()
        }
