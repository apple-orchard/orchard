import os
import re
import logging
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
        self.logger = logging.getLogger(__name__)

    def extract_text_from_file(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract text from various file formats"""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path_obj}")

        self.logger.info(f"Extracting text from {file_path_obj.suffix.upper()} file: {file_path_obj.name}")

        metadata = {
            "source": str(file_path_obj),
            "filename": file_path_obj.name,
            "file_type": file_path_obj.suffix.lower(),
            "file_size": file_path_obj.stat().st_size
        }

        # Log file size for user awareness
        file_size_mb = metadata["file_size"] / (1024 * 1024)
        self.logger.info(f"File size: {file_size_mb:.2f} MB")

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

            # Log extraction results
            self.logger.info(f"Extracted {metadata['char_count']:,} characters, {metadata['word_count']:,} words")

        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path_obj}: {str(e)}")
            raise Exception(f"Error processing file {file_path_obj}: {str(e)}")

        return text, metadata

    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        self.logger.info("Processing PDF pages...")
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            self.logger.info(f"PDF has {total_pages} pages")

            for i, page in enumerate(pdf_reader.pages, 1):
                if i % 10 == 0 or i == total_pages:  # Progress update every 10 pages or on last page
                    self.logger.info(f"Processing page {i}/{total_pages}")
                text += page.extract_text() + "\n"

        self.logger.info(f"PDF text extraction completed")
        return text

    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        self.logger.info("Processing DOCX paragraphs...")
        doc = docx.Document(file_path)
        text = ""
        paragraph_count = len(doc.paragraphs)
        self.logger.info(f"Document has {paragraph_count} paragraphs")

        for i, paragraph in enumerate(doc.paragraphs, 1):
            if paragraph_count > 100 and i % 50 == 0:  # Progress for large documents
                self.logger.info(f"Processing paragraph {i}/{paragraph_count}")
            text += paragraph.text + "\n"

        self.logger.info(f"DOCX text extraction completed")
        return text

    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        self.logger.info("Reading text file...")
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        self.logger.info(f"Text file reading completed")
        return text

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        self.logger.info(f"Chunking text into segments (chunk_size={settings.chunk_size}, overlap={settings.chunk_overlap})...")
        chunks = self.text_splitter.split_text(text)
        self.logger.info(f"Created {len(chunks)} chunks")

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
            metadata = {}

        # Ensure required metadata fields are present
        metadata.setdefault("source", "text_input")
        metadata.setdefault("char_count", len(text))
        metadata.setdefault("word_count", len(text.split()))

        self.logger.info(f"Processing raw text input - {metadata['char_count']:,} characters, {metadata['word_count']:,} words")
        return self.chunk_text(text, metadata)

    def process_directory(self, directory_path: str, recursive: bool = True,
                         additional_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process all supported files in a directory"""
        directory_path_obj = Path(directory_path)

        if not directory_path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path_obj}")

        supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        all_chunks = []

        # First, count files for progress tracking
        pattern = "**/*" if recursive else "*"
        all_files = list(directory_path_obj.glob(pattern))
        supported_files = [f for f in all_files if f.is_file() and f.suffix.lower() in supported_extensions]

        mode = "recursively" if recursive else "non-recursively"
        self.logger.info(f"Scanning directory {mode}: {directory_path}")
        self.logger.info(f"Found {len(supported_files)} supported files (PDF, DOCX, DOC, TXT)")

        if not supported_files:
            self.logger.warning("No supported files found in directory")
            return all_chunks

        # Process each file with progress updates
        for i, file_path in enumerate(supported_files, 1):
            try:
                self.logger.info(f"📄 Processing file {i}/{len(supported_files)}: {file_path.name}")
                chunks = self.process_file(str(file_path), additional_metadata)
                all_chunks.extend(chunks)
                self.logger.info(f"  ✅ Completed {file_path.name} - {len(chunks)} chunks created")
            except Exception as e:
                self.logger.error(f"  ❌ Error processing {file_path.name}: {e}")
                continue

        self.logger.info(f"📁 Directory processing completed - {len(all_chunks)} total chunks from {len(supported_files)} files")
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