# Example Documentation

This is a sample markdown file to demonstrate intelligent header-based chunking.

## Introduction

The RAG system now supports intelligent parsing of Markdown files. When you upload a Markdown file, it will:

- Parse the document structure
- Split content based on headers
- Preserve the hierarchy of sections
- Maintain relationships between chunks

## Features

### Markdown Parsing

The system uses the MarkdownNodeParser to understand the document structure. This means:

1. Headers create natural boundaries for chunks
2. The header hierarchy is preserved in metadata
3. Code blocks within markdown are kept intact

### Code Parsing

For code files, the system provides:

1. **Language Detection**: Automatically detects the programming language
2. **Smart Boundaries**: Chunks respect function and class boundaries where possible
3. **Syntax Awareness**: Uses language-specific separators

## Usage Example

To use the new functionality:

```bash
# Upload a markdown file
curl -X POST "http://localhost:8011/ingest" \
  -F "file=@example.md" \
  -F "metadata={\"category\": \"documentation\"}"
```

## Conclusion

This intelligent parsing ensures that your documents are chunked in a way that preserves their semantic meaning and structure. 