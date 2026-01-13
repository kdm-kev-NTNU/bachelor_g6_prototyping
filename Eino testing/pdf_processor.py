"""
PDF processing using pdfplumber for parsing energy advice documents.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import tiktoken

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("[WARN] pdfplumber ikke installert. Bruk: pip install pdfplumber")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimate
        return len(text.split()) * 1.3


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        overlap: Overlap size in tokens
    
    Returns:
        List of text chunks
    """
    if not text.strip():
        return []
    
    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = count_tokens(para)
        
        # If paragraph is too large, split it
        if para_tokens > chunk_size:
            # Add current chunk if exists
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            # Split large paragraph by sentences
            sentences = para.split('. ')
            for sent in sentences:
                sent_tokens = count_tokens(sent)
                if current_tokens + sent_tokens > chunk_size and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    # Keep overlap
                    overlap_text = '\n\n'.join(current_chunk[-overlap//20:])
                    current_chunk = [overlap_text, sent] if overlap_text else [sent]
                    current_tokens = count_tokens('\n\n'.join(current_chunk))
                else:
                    current_chunk.append(sent)
                    current_tokens += sent_tokens
        else:
            # Check if adding paragraph exceeds chunk size
            if current_tokens + para_tokens > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                # Keep overlap
                overlap_text = '\n\n'.join(current_chunk[-overlap//20:])
                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_tokens = count_tokens('\n\n'.join(current_chunk))
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF using pdfplumber.
    
    Returns:
        Dictionary with 'text', 'pages', 'metadata'
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber ikke installert. Installer med: pip install pdfplumber")
    
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF ikke funnet: {pdf_path}")
    
    text_parts = []
    pages = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text from page
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    text_parts.append(page_text)
                    pages.append(page_num)
    except Exception as e:
        raise Exception(f"Feil ved PDF-behandling med pdfplumber: {str(e)}")
    
    full_text = '\n\n'.join(text_parts)
    
    return {
        "text": full_text,
        "pages": pages,
        "metadata": {
            "source_file": pdf_path_obj.name,
            "file_path": str(pdf_path),
            "num_pages": len(pages),
            "doc_type": "energy_advice"
        }
    }


def process_pdf_directory(pdf_dir: str = "pdf", chunk_size: int = 200, 
                          chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Process all PDFs in directory and return chunks.
    
    Returns:
        List of chunk dictionaries with text, metadata, and source info
    """
    pdf_dir_path = Path(pdf_dir)
    if not pdf_dir_path.exists():
        raise FileNotFoundError(f"PDF-mappe ikke funnet: {pdf_dir}")
    
    all_chunks = []
    
    # Find all PDF files
    pdf_files = list(pdf_dir_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"[WARN] Ingen PDF-filer funnet i {pdf_dir}")
        return []
    
    print(f"[INFO] Fant {len(pdf_files)} PDF-filer")
    
    for pdf_file in pdf_files:
        try:
            print(f"[INFO] Behandler {pdf_file.name}...")
            result = extract_text_from_pdf(str(pdf_file))
            
            if not result["text"].strip():
                print(f"[WARN] {pdf_file.name}: Ingen tekst funnet")
                continue
            
            # Chunk the text
            chunks = chunk_text(result["text"], chunk_size, chunk_overlap)
            
            # Create chunk entries with metadata
            for i, chunk_text_content in enumerate(chunks):
                # Estimate page number (rough)
                page_estimate = None
                if result["pages"]:
                    page_estimate = result["pages"][min(
                        i * len(result["pages"]) // len(chunks),
                        len(result["pages"]) - 1
                    )]
                
                chunk_entry = {
                    "text": chunk_text_content,
                    "metadata": {
                        **result["metadata"],
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "page": page_estimate,
                        "tokens": count_tokens(chunk_text_content)
                    }
                }
                all_chunks.append(chunk_entry)
            
            print(f"[OK] {pdf_file.name}: {len(chunks)} chunks")
            
        except Exception as e:
            print(f"[ERROR] Feil ved behandling av {pdf_file.name}: {e}")
            continue
    
    print(f"[OK] Totalt {len(all_chunks)} chunks generert")
    return all_chunks


if __name__ == "__main__":
    # Test PDF processing
    if PDFPLUMBER_AVAILABLE:
        chunks = process_pdf_directory()
        print(f"\nFørste chunk eksempel:")
        if chunks:
            print(chunks[0]["text"][:500])
            print(f"\nMetadata: {chunks[0]['metadata']}")
    else:
        print("pdfplumber ikke tilgjengelig. Installer med: pip install pdfplumber")
