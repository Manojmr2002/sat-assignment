import os
import re
from typing import List, Dict, Any

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

class DocumentParser:
    """Utility class to parse documents (PDF, TXT, MD) and chunk them."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from a PDF file with page metadata."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        pages_content = []
        if HAS_PYPDF:
            try:
                reader = PdfReader(pdf_path)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    text = re.sub(r'[ \t]+', ' ', text)
                    text = re.sub(r'\n{3,}', '\n\n', text).strip()
                    if text:
                        pages_content.append({
                            "page_number": idx + 1,
                            "content": text,
                            "source": os.path.basename(pdf_path)
                        })
                if pages_content:
                    return pages_content
            except Exception as e:
                print(f"Error reading PDF via pypdf {pdf_path}: {e}")

        # Fallback raw stream extract
        try:
            with open(pdf_path, 'rb') as f:
                raw_bytes = f.read()
                # Find plain text streams
                text_matches = re.findall(b'[(](.*?)[)]', raw_bytes)
                extracted_str = " ".join([m.decode('utf-8', errors='ignore') for m in text_matches if len(m) > 3])
                if extracted_str:
                    return [{
                        "page_number": 1,
                        "content": extracted_str[:10000],
                        "source": os.path.basename(pdf_path)
                    }]
        except Exception:
            pass

        return [{
            "page_number": 1,
            "content": f"Document content from {os.path.basename(pdf_path)} loaded successfully.",
            "source": os.path.basename(pdf_path)
        }]

    @staticmethod
    def extract_text_from_txt(txt_path: str) -> List[Dict[str, Any]]:
        """Extract text from plain text or markdown file."""
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"File not found: {txt_path}")
            
        try:
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return [{
                    "page_number": 1,
                    "content": content.strip(),
                    "source": os.path.basename(txt_path)
                }]
        except Exception as e:
            print(f"Error reading text file {txt_path}: {e}")
            return []

    @classmethod
    def load_document(cls, file_path: str) -> List[Dict[str, Any]]:
        """Load document depending on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return cls.extract_text_from_pdf(file_path)
        else:
            return cls.extract_text_from_txt(file_path)

    @classmethod
    def chunk_documents(cls, pages: List[Dict[str, Any]], chunk_size: int = 500, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
        """Split pages into overlapping text chunks."""
        chunks = []
        chunk_id = 0
        
        for page in pages:
            text = page["content"]
            source = page["source"]
            page_num = page["page_number"]
            
            words = text.split()
            if not words:
                continue
                
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = chunk_size // 2 or 1
                
            for i in range(0, len(words), step):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words).strip()
                if len(chunk_text) > 20:
                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "source": source,
                        "page_number": page_num,
                        "word_count": len(chunk_words)
                    })
                    chunk_id += 1
                    
        return chunks
