import os
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Import chunking registry for smart chunking
try:
    from plugins.chunking_registry import chunking_registry
    logger.info("Smart chunking plugins available")
except ImportError:
    chunking_registry = None
    logger.info("Smart chunking plugins not available, using regular chunking")

# Supported code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.sql', '.sh', '.bash', '.zsh', '.ps1', '.yaml', '.yml', '.json', '.xml',
    '.html', '.css', '.scss', '.sass', '.less', '.vue', '.dart', '.lua',
    '.perl', '.m', '.mm', '.f', '.f90', '.jl', '.nim', '.zig', '.toml', '.ini'
}

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Code-specific text splitter with language-aware separators
        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=[
                "\n\nclass ",
                "\n\ndef ",
                "\n\nfunction ",
                "\n\nexport ",
                "\n\nimport ",
                "\n\n// ",
                "\n\n/* ",
                "\n\n# ",
                "\n\n",
                "\n",
                " ",
                ""
            ]
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
            elif file_path_obj.suffix.lower() in ['.md', '.markdown']:
                text = self._extract_from_markdown(file_path_obj)
                metadata["content_type"] = "markdown"
            elif file_path_obj.suffix.lower() in CODE_EXTENSIONS:
                text = self._extract_from_code(file_path_obj)
                metadata["content_type"] = "code"
                metadata["language"] = self._detect_language(file_path_obj.suffix.lower())
            else:
                raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
            
            metadata["char_count"] = len(text)
            metadata["word_count"] = len(text.split())
            metadata["line_count"] = len(text.splitlines())
            
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
    
    def _extract_from_markdown(self, file_path: Path) -> str:
        """Extract text from Markdown file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _extract_from_code(self, file_path: Path) -> str:
        """Extract text from code file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encodings if UTF-8 fails
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Unable to decode file {file_path}")
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.ps1': 'powershell',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.vue': 'vue',
            '.dart': 'dart',
            '.lua': 'lua',
            '.perl': 'perl',
            '.m': 'matlab',
            '.f': 'fortran',
            '.f90': 'fortran',
            '.jl': 'julia',
            '.nim': 'nim',
            '.zig': 'zig',
            '.toml': 'toml',
            '.ini': 'ini'
        }
        return language_map.get(extension, 'unknown')
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        # Use appropriate splitter based on content type
        if metadata.get("content_type") == "code":
            chunks = self.code_splitter.split_text(text)
        else:
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
    
    def process_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None,
                     use_smart_chunking: bool = True) -> List[Dict[str, Any]]:
        """Process a single file: extract text and chunk it"""
        logger.info(f"Processing file: {file_path} (smart_chunking={'enabled' if use_smart_chunking else 'disabled'})")
        
        # Try smart chunking first if enabled and available
        if use_smart_chunking and chunking_registry:
            logger.debug("Attempting to use smart chunking plugin")
            chunks = chunking_registry.process_file_with_best_plugin(file_path, additional_metadata)
            if chunks is not None:
                logger.info(f"Successfully processed with smart chunking: {len(chunks)} chunks created")
                return chunks
            else:
                logger.debug("Smart chunking not applicable for this file type")
        
        # Fall back to regular processing
        logger.info("Using regular chunking (RecursiveCharacterTextSplitter)")
        text, metadata = self.extract_text_from_file(file_path)
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        chunks = self.chunk_text(text, metadata)
        logger.info(f"Regular chunking complete: {len(chunks)} chunks created")
        return chunks
    
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
        
        logger.info(f"Processing directory: {directory_path} (recursive={recursive})")
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown'} | CODE_EXTENSIONS
        all_chunks = []
        
        pattern = "**/*" if recursive else "*"
        files_to_process = [f for f in directory_path_obj.glob(pattern) 
                           if f.is_file() and f.suffix.lower() in supported_extensions]
        logger.info(f"Found {len(files_to_process)} files to process")
        
        for i, file_path in enumerate(files_to_process, 1):
            try:
                logger.info(f"Processing file {i}/{len(files_to_process)}: {file_path.name}")
                chunks = self.process_file(str(file_path), additional_metadata)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"Directory processing complete: {len(all_chunks)} total chunks created")
        return all_chunks
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters (optional)
        text = re.sub(r'[^\w\s\.\,\!\?\;]', '', text)
        return text.strip()

# Global document processor instance
document_processor = DocumentProcessor() 