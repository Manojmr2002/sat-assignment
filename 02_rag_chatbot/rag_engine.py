import os
import sys
from typing import List, Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.document_parser import DocumentParser
from shared.vector_db import LocalVectorDB
from shared.llm_provider import llm

class RAGEngine:
    """RAG Chatbot Engine managing document embeddings, FAISS vector retrieval, and LLM synthesis."""

    def __init__(self, name: str = "rag_chatbot"):
        self.vector_db = LocalVectorDB(name=name)
        self.indexed_files: List[Dict[str, Any]] = []

    def ingest_pdf(self, file_path: str) -> Dict[str, Any]:
        """Load, chunk, and index a PDF into the vector store."""
        pages = DocumentParser.load_document(file_path)
        chunks = DocumentParser.chunk_documents(pages, chunk_size=400, chunk_overlap=80)
        
        added_count = self.vector_db.add_documents(chunks)
        filename = os.path.basename(file_path)
        
        file_info = {
            "filename": filename,
            "path": file_path,
            "pages": len(pages),
            "chunks": added_count
        }
        self.indexed_files.append(file_info)
        return file_info

    def answer_query(
        self,
        query: str,
        mode: str = "hybrid",  # 'hybrid', 'doc_only', 'llm_only'
        top_k: int = 4,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant context and generate response synthesizing document facts & LLM knowledge."""
        retrieved_chunks = []
        context_str = ""

        if mode in ["hybrid", "doc_only"]:
            retrieved_chunks = self.vector_db.similarity_search(query, k=top_k, threshold=0.03)
            
            if retrieved_chunks:
                context_parts = []
                for idx, c in enumerate(retrieved_chunks):
                    context_parts.append(
                        f"[Snippet {idx+1}] (Source: {c['source']}, Page {c['page_number']}):\n{c['text']}"
                    )
                context_str = "\n\n".join(context_parts)

        # Build prompt based on mode
        if mode == "doc_only":
            if not retrieved_chunks:
                return {
                    "answer": "I could not find any relevant information in the uploaded document(s) to answer your question in strict document-only mode. Try switching to **Hybrid Mode** or uploading additional documents.",
                    "sources": [],
                    "mode": mode
                }
            system_prompt = (
                "You are an accurate, strict AI Assistant. You answer questions based ONLY on the provided document snippets. "
                "Do not introduce outside information. If the answer is not contained in the text, clearly state that."
            )
            prompt = f"""
DOCUMENT SNIPPETS:
\"\"\"
{context_str}
\"\"\"

USER QUESTION: {query}

Provide a direct, accurate answer quoting or citing the relevant document sections.
"""
        elif mode == "hybrid":
            system_prompt = (
                "You are a knowledgeable AI Assistant with Retrieval-Augmented Generation (RAG). "
                "Your task is to synthesize answers using BOTH the uploaded document context AND your broader knowledge. "
                "1. Explicitly highlight facts retrieved directly from the document. "
                "2. Seamlessly supplement with broader general knowledge and context where helpful."
            )
            prompt = f"""
DOCUMENT CONTEXT (Retrieved from uploaded PDFs):
\"\"\"
{context_str if context_str else "No direct document snippets found."}
\"\"\"

USER QUESTION: {query}

INSTRUCTIONS:
Synthesize a comprehensive answer. Structure your response with:
- **Direct Findings from Documents**: (Detail what the uploaded documents say)
- **Broader Insights & LLM Knowledge**: (Add helpful context, practical applications, or related concepts)
- **Summary Conclusion**
"""
        else: # llm_only
            system_prompt = "You are a helpful and knowledgeable AI assistant."
            prompt = query

        response_text = llm.generate(prompt=prompt, system_prompt=system_prompt, model=model, temperature=0.6)

        # Prepare source citations
        sources = []
        for c in retrieved_chunks:
            sources.append({
                "source": c.get("source", "Document"),
                "page": c.get("page_number", 1),
                "score": c.get("score", 0.0),
                "preview": c.get("text", "")[:180] + "..."
            })

        return {
            "answer": response_text,
            "sources": sources,
            "mode": mode,
            "context_count": len(retrieved_chunks)
        }

    def clear(self):
        """Clear all indexed documents and vector index."""
        self.vector_db.clear()
        self.indexed_files = []
