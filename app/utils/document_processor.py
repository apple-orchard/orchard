import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings
import json

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_file(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract text from various file formats"""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path_obj}")
        
        metadata = {
            "source": str(file_path_obj),
            "filename": file_path_obj.name,
            "file_type": file_path_obj.suffix.lower(),
            "file_size": file_path_obj.stat().st_size
        }
        
        text = ""
        
        try:
            if file_path_obj.suffix.lower() == '.pdf':
                text = self._extract_from_pdf(file_path_obj)
            elif file_path_obj.suffix.lower() in ['.docx', '.doc']:
                text = self._extract_from_docx(file_path_obj)
            elif file_path_obj.suffix.lower() == '.txt':
                text = self._extract_from_txt(file_path_obj)
            else:
                raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
            
            metadata["char_count"] = len(text)
            metadata["word_count"] = len(text.split())
            
        except Exception as e:
            raise Exception(f"Error processing file {file_path_obj}: {str(e)}")
        
        return text, metadata
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        chunks = self.text_splitter.split_text(text)
        
        chunked_documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_count": len(chunks),
                "chunk_char_count": len(chunk),
                "chunk_word_count": len(chunk.split())
            })
            
            chunked_documents.append({
                "content": chunk,
                "metadata": chunk_metadata
            })
        
        return chunked_documents
    
    def process_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process a single file: extract text and chunk it"""
        text, metadata = self.extract_text_from_file(file_path)
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return self.chunk_text(text, metadata)
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process raw text: chunk it with metadata"""
        if metadata is None:
            metadata = {
                "source": "text_input",
                "char_count": len(text),
                "word_count": len(text.split())
            }
        
        return self.chunk_text(text, metadata)
    
    def process_directory(self, directory_path: str, recursive: bool = True, 
                         additional_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process all supported files in a directory"""
        directory_path_obj = Path(directory_path)
        
        if not directory_path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path_obj}")
        
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        all_chunks = []
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory_path_obj.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    chunks = self.process_file(str(file_path), additional_metadata)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
        
        return all_chunks
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters (optional)
        text = re.sub(r'[^\w\s\.\,\!\?\;]', '', text)
        return text.strip()

def serialize_metadata(metadata: dict) -> dict:
    """Ensure all metadata values are primitive types, serializing dicts/lists to JSON strings."""
    if not isinstance(metadata, dict):
        return metadata
    result = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            result[k] = v
        else:
            result[k] = json.dumps(v)
    return result

# Global document processor instance
document_processor = DocumentProcessor() 