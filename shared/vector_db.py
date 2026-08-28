import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LocalVectorDB:
    """
    In-memory and persistent Vector Store.
    Uses TF-IDF + Cosine Similarity by default, or SentenceTransformers if loaded.
    Provides FAISS-like index interface with cosine distance / similarity ranking.
    """
    def __init__(self, name: str = "default"):
        self.name = name
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=10000, ngram_range=(1, 2))
        self.vectors = None
        self.is_fitted = False
        self._st_model = None

    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """Add list of document chunk dicts {id, text, source, page_number}."""
        if not chunks:
            return 0
            
        start_id = len(self.documents)
        for i, chunk in enumerate(chunks):
            doc = dict(chunk)
            if "id" not in doc:
                doc["id"] = start_id + i
            self.documents.append(doc)
            
        self._reindex()
        return len(chunks)

    def _reindex(self):
        """Fit vectorizer and build document matrix."""
        if not self.documents:
            self.vectors = None
            self.is_fitted = False
            return
            
        corpus = [doc.get("text", "") for doc in self.documents]
        try:
            self.vectors = self.vectorizer.fit_transform(corpus)
            self.is_fitted = True
        except Exception as e:
            print(f"Error vectorizing corpus: {e}")
            self.is_fitted = False

    def similarity_search(self, query: str, k: int = 4, threshold: float = 0.05) -> List[Dict[str, Any]]:
        """Search top-k most relevant chunks for a query string."""
        if not self.documents or not self.is_fitted or not query.strip():
            return []
            
        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.vectors).flatten()
            
            # Sort indices by score descending
            top_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= threshold or len(results) == 0:  # Always return at least top 1 if available
                    doc_copy = dict(self.documents[idx])
                    doc_copy["score"] = round(score, 4)
                    results.append(doc_copy)
                if len(results) >= k:
                    break
                    
            return results
        except Exception as e:
            print(f"Similarity search error: {e}")
            # Fallback simple keyword match
            query_words = set(query.lower().split())
            scored = []
            for doc in self.documents:
                text_words = set(doc.get("text", "").lower().split())
                overlap = len(query_words.intersection(text_words))
                scored.append((overlap, doc))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [dict(doc, score=0.5) for count, doc in scored[:k] if count > 0]

    def clear(self):
        """Clear the vector store."""
        self.documents = []
        self.vectors = None
        self.is_fitted = False

    def count(self) -> int:
        """Return total number of indexed chunks."""
        return len(self.documents)
