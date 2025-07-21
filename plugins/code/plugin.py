"""Code chunking plugin for intelligent code file processing."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from llama_index.core.node_parser import CodeSplitter
from llama_index.core.schema import Document as LlamaDocument
from plugins.base import ChunkingPlugin
from app.core.config import settings

logger = logging.getLogger(__name__)

# Supported code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.sql', '.sh', '.bash', '.zsh', '.ps1', '.yaml', '.yml', '.json', '.xml',
    '.html', '.css', '.scss', '.sass', '.less', '.vue', '.dart', '.lua',
    '.perl', '.m', '.mm', '.f', '.f90', '.jl', '.nim', '.zig', '.toml', '.ini'
}

# Language mapping for CodeSplitter
LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript', '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
    '.c': 'c', '.h': 'c',
    '.hpp': 'cpp', '.hh': 'cpp', '.hxx': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin', '.kts': 'kotlin',
    '.scala': 'scala',
    '.r': 'r',
    '.sql': 'sql',
    '.sh': 'bash', '.bash': 'bash', '.zsh': 'bash',
    '.ps1': 'powershell',
    '.html': 'html', '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss', '.sass': 'scss',
    '.vue': 'vue',
    '.lua': 'lua',
    '.m': 'objc', '.mm': 'objc',
    '.jl': 'julia',
}


class CodeChunkingPlugin(ChunkingPlugin):
    """Plugin for intelligent code file chunking using language-aware splitting."""
    
    name = "code"
    supported_extensions = CODE_EXTENSIONS
    
    def __init__(self):
        super().__init__()
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def can_process(self, file_path: str) -> bool:
        """Check if this plugin can process the given file."""
        path = Path(file_path)
        return path.suffix.lower() in self.supported_extensions
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension."""
        return LANGUAGE_MAP.get(extension.lower(), 'text')
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process a code file into chunks using language-aware splitting."""
        try:
            path = Path(file_path)
            logger.info(f"Processing code file: {path.name}")
            
            # Read the file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try alternative encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"Unable to decode file {file_path}")
            
            # Detect language
            language = self._detect_language(path.suffix)
            
            # Create metadata
            file_metadata = {
                "source": str(path),
                "filename": path.name,
                "file_type": path.suffix.lower(),
                "content_type": "code",
                "language": language,
                "line_count": len(content.splitlines())
            }
            
            if metadata:
                file_metadata.update(metadata)
            
            # Create LlamaIndex Document
            document = LlamaDocument(
                text=content,
                metadata=file_metadata
            )
            
            # Use CodeSplitter for supported languages, fallback to regular chunking
            if language in ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 
                           'csharp', 'go', 'rust', 'ruby', 'php']:
                try:
                    splitter = CodeSplitter(
                        language=language,
                        chunk_lines=40,  # Approximately equivalent to chunk_size
                        chunk_lines_overlap=5,
                        max_chars=self.chunk_size
                    )
                    nodes = splitter.get_nodes_from_documents([document])
                    logger.info(f"Using CodeSplitter for {language}")
                except Exception as e:
                    logger.warning(f"CodeSplitter failed for {language}, falling back to regular chunking: {e}")
                    nodes = self._fallback_chunk(document)
            else:
                # Use fallback chunking for unsupported languages
                nodes = self._fallback_chunk(document)
            
            # Convert nodes to our chunk format
            chunks = []
            for i, node in enumerate(nodes):
                chunk_metadata = file_metadata.copy()
                
                # Add node-specific metadata
                if hasattr(node, 'metadata'):
                    for key, value in node.metadata.items():
                        if key not in chunk_metadata:
                            chunk_metadata[key] = value
                
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_count": len(nodes),
                    "chunk_id": node.node_id if hasattr(node, 'node_id') else f"{path.name}_chunk_{i}",
                    "chunking_method": "code_aware"
                })
                
                chunks.append({
                    "content": node.get_content() if hasattr(node, 'get_content') else str(node),
                    "metadata": chunk_metadata
                })
            
            logger.info(f"Successfully chunked code file into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing code file {file_path}: {str(e)}")
            raise
    
    def _fallback_chunk(self, document: LlamaDocument) -> List:
        """Fallback chunking method for unsupported languages."""
        from llama_index.core.node_parser import SentenceSplitter
        
        # Use SentenceSplitter with code-friendly separators
        splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator="\n",
            paragraph_separator="\n\n",
            secondary_chunking_regex="[^,.;。？！]+[,.;。？！]?"
        )
        
        return splitter.get_nodes_from_documents([document])
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the text."""
        # Code typically has more tokens per character than regular text
        return len(text) // 3 