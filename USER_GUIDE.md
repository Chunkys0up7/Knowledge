# Knowledge Management System User Guide

This comprehensive guide explains how to use the Knowledge Management System to process, manage, and retrieve information from large document collections.

## Contents

- [Introduction](#introduction)
- [Core Concepts](#core-concepts)
- [Using the Web Interface](#using-the-web-interface)
- [Command Line Usage](#command-line-usage)
- [Bulk Document Processing](#bulk-document-processing)
- [Citation System](#citation-system)
- [Knowledge Maps and Organization](#knowledge-maps-and-organization)
- [Search and RAG Usage](#search-and-rag-usage)
- [Advanced Features](#advanced-features)
- [Workflows and Automation](#workflows-and-automation)
- [Best Practices](#best-practices)

## Introduction

The Knowledge Management System transforms documents into richly connected knowledge bases with citation tracking, structured metadata, and RAG (Retrieval-Augmented Generation) compatibility. The system is designed to handle large document volumes while maintaining precise citation information for each document and chunk.

### Key Capabilities

- Process code, markdown, text, PDFs, and other document formats
- Extract structure and metadata
- Generate citation information
- Organize knowledge into repositories
- Create knowledge maps
- Support RAG with precise citation tracking

## Core Concepts

Understanding these key concepts will help you use the system effectively:

### Knowledge Base (KB)

A Knowledge Base is a dedicated Git repository containing processed documents, metadata, and citation information. Each KB has:

- Raw document storage
- Processed markdown versions
- Metadata for each document
- Citation information
- Chunks for RAG
- Documentation and knowledge maps

### Document Processing

When a document is processed:

1. Metadata is extracted (creation date, modification date, content type, etc.)
2. The document is converted to markdown (if not already)
3. Structure is preserved and enhanced
4. Citation information is generated
5. The document is stored in the KB repository

### Chunking

Documents are divided into semantic chunks for RAG with these properties:

- Each chunk maintains context
- Chunks include citation information
- Chunks are sized appropriately for embedding and retrieval
- Overlapping text ensures concept continuity

### Citations

The citation system ensures that every document chunk can be traced back to its source with precise location information:

- Code files: class, function, and line number information
- Markdown: section headers and hierarchy
- PDFs: page numbers
- All documents: version, author, title, and repository location

## Using the Web Interface

The web interface provides a user-friendly way to manage knowledge bases and process documents.

### Creating a Knowledge Base

1. Navigate to the web interface at http://localhost:5000
2. Click the "Create New Knowledge Base" button
3. Enter a name (e.g., "technical_docs")
4. Provide an optional description and owner
5. Click "Create"

### Uploading and Processing Documents

1. Go to the "Upload" tab
2. Select your knowledge base from the dropdown
3. Drag and drop files into the upload area (up to 100 files at once)
4. Check "Automatically chunk documents for RAG" if desired
5. Check "Create knowledge maps" if desired
6. Click "Upload and Process Documents"
7. Monitor progress in the upload status area

### Monitoring Tasks

1. Go to the "Tasks" tab to see all active and completed tasks
2. Click "View Details" on any task to see full information
3. Active tasks show a progress bar with percentage completion
4. Completed tasks show result summaries

### Viewing Knowledge Base Status

1. Go to the "Knowledge Bases" tab
2. Find your knowledge base in the list
3. Click "View Details" to see statistics and information
4. This shows counts of raw files, processed files, metadata, citations, and chunks

### Searching the Knowledge Base

1. Go to the "Search" tab
2. Select your knowledge base from the dropdown
3. Enter your search query
4. View results with their citations

## Command Line Usage

The command line interface provides powerful tools for managing knowledge bases through the terminal.

### Creating a Knowledge Base

```bash
python src/cli.py kb create --name technical_docs --description "Technical Documentation" --owner "Your Name"
```

### Listing Knowledge Bases

```bash
python src/cli.py kb list
```

### Checking Knowledge Base Status

```bash
python src/cli.py kb status --name technical_docs
```

### Processing Documents

Process a single document:

```bash
python src/cli.py ingest --path /path/to/document.pdf --kb technical_docs
```

Process an entire directory:

```bash
python src/cli.py ingest --path /path/to/documents --kb technical_docs
```

### Chunking Documents

Chunk a specific document:

```bash
python src/cli.py chunk --kb technical_docs --doc-id <document_id>
```

Chunk all documents in a knowledge base:

```bash
python src/cli.py chunk --kb technical_docs --all
```

### Creating Knowledge Maps

Create a map of all documents:

```bash
python src/cli.py map create --name "All Documents" --kb technical_docs --all
```

Create a map from a list of document IDs:

```bash
python src/cli.py map create --name "Selected Documents" --kb technical_docs --documents doc_list.txt
```

### Creating Process Documentation

```bash
python src/cli.py process create --name "Document Processing" --content process.md --kb technical_docs
```

### Searching

```bash
python src/cli.py search "query terms" --kb technical_docs
```

## Bulk Document Processing

For processing large volumes of documents efficiently, follow these guidelines:

### Web Interface Method (Recommended for 10-100 documents)

1. Start the web server: `python src/ui/app.py`
2. Go to http://localhost:5000
3. Navigate to the "Upload" tab
4. Select your knowledge base
5. Drag and drop all documents (up to 100 at once)
6. Enable automatic chunking and map creation
7. Click "Upload and Process Documents"
8. The system will:
   - Process files in batches to manage memory usage
   - Create citation information
   - Generate knowledge maps
   - Chunk documents for RAG
   - Commit changes to the KB repository

### Command Line Method (For automation and scripting)

For processing large batches from scripts:

```bash
# Process all documents in a directory
python src/cli.py ingest --path /path/to/large/directory --kb your_kb_name

# Chunk all documents
python src/cli.py chunk --kb your_kb_name --all

# Create maps
python src/cli.py map create --name "All Documents" --kb your_kb_name --all
```

### Resource Management

The system is designed to handle large document volumes efficiently:

- Documents are processed in batches (configurable batch size)
- Memory usage is controlled through resource limits
- Processing is multi-threaded but with controlled concurrency
- Resources are released between batches
- Progress is tracked and reported in real-time

## Citation System

The citation system is a core feature that ensures every chunk of knowledge can be traced back to its source with precise location information.

### Citation Information Includes

For all documents:
- Document ID
- Document title
- Author (if available)
- Version
- Processing date
- Repository location

Additional information by document type:

#### Code Files

- Language
- Class/function name
- Line numbers
- Documentation comments

#### Markdown

- Section headers
- Header hierarchy
- Line numbers

#### PDFs

- Page numbers
- Section information (if available)

### How Citations Are Created

1. During document processing, the system extracts structural information
2. The CitationProcessor analyzes the document structure
3. Citation information is stored as JSON in the KB repository
4. When documents are chunked, each chunk is associated with its citation
5. Citation data is included with RAG results

### Viewing Citation Information

In the command line:

```bash
# Get document metadata including citation info
cat /data/knowledge_bases/your_kb_name/metadata/<doc_id>.json

# Get citation information
cat /data/knowledge_bases/your_kb_name/citations/<doc_id>_citation.json

# Get chunk metadata with citation
cat /data/knowledge_bases/your_kb_name/chunks/metadata/<chunk_id>.json
```

In search results, citations appear with each result showing the document source and precise location.

## Knowledge Maps and Organization

Knowledge maps provide visual and structural organization for your knowledge base.

### Types of Knowledge Maps

The system can generate several types of maps:

- **Document Type Maps**: Group documents by content type (code, markdown, etc.)
- **Topic Maps**: Group documents based on content similarity
- **Process Maps**: Show workflow and process documentation
- **Reference Maps**: Show relationships between documents

### Viewing Knowledge Maps

Knowledge maps are stored as markdown files with Mermaid diagrams:

```bash
# List knowledge maps
ls /data/knowledge_bases/your_kb_name/documentation/maps/

# View a specific map
cat /data/knowledge_bases/your_kb_name/documentation/maps/technical_docs_map.md
```

When viewed in a markdown renderer that supports Mermaid, these maps display as interactive diagrams.

### Knowledge Base Organization

Each KB repository follows this structure:

```
/kb_name/
├── raw/              # Original documents
├── processed/        # Processed markdown versions
│   ├── code/         # Code files
│   ├── markdown/     # Documentation files
│   └── documents/    # Other document types
├── metadata/         # Document metadata
├── citations/        # Citation information
├── chunks/           # Chunked content for RAG
│   ├── text/         # Plain text chunks
│   └── metadata/     # Chunk metadata with citation info
├── vectors/          # Vector embeddings
├── workflows/        # Processing workflow records
├── pdfs/             # PDF versions for citation
├── documentation/    # KB documentation
│   ├── processes/    # Process documentation
│   ├── maps/         # Knowledge maps
│   └── guides/       # User guides
└── index/            # Index files
```

## Search and RAG Usage

The system provides multiple ways to retrieve information:

### Basic Search

Using the CLI:

```bash
python src/cli.py search "query terms" --kb your_kb_name
```

Using the web interface:
1. Go to the "Search" tab
2. Select your knowledge base
3. Enter your query
4. View results with citations

### Programmatic RAG Usage

```python
from src.main import KnowledgeSystem

# Initialize system
system = KnowledgeSystem()

# Generate a response with RAG
response = system.generate_response("How does the authentication system work?")
print(response)

# The response includes citations to source documents
```

## Advanced Features

### Custom Document Handlers

You can extend the system to handle custom document types:

1. Create a handler class that extracts text and structure
2. Register it in the SmartIngestor's SUPPORTED_FORMATS dictionary
3. The system will use your handler for the specified file types

### Workflow Automation

For continuous processing of document directories:

```bash
# Set up a directory watcher
python src/workflow/document_workflow.py --watch --config config.yaml
```

This will:
- Monitor specified directories for new files
- Process new documents automatically
- Create workflows for batches of documents
- Update the knowledge base with new content

### Git Integration

Each knowledge base is a Git repository, allowing:
- Version history of all documents
- Collaboration through branches and pull requests
- Rollback of changes if needed
- Full audit trail of document changes

## Workflows and Automation

The system supports automated workflows for document processing.

### Document Processing Workflow

The standard document processing workflow:

1. **Ingestion**: Raw documents are copied to the KB
2. **Processing**: Documents are converted to markdown, structure is extracted
3. **Metadata**: Document metadata is created
4. **Citation**: Citation information is generated
5. **Chunking**: Documents are chunked for RAG
6. **Indexing**: Chunks are indexed for search and retrieval
7. **Mapping**: Knowledge maps are created

### Automated Directory Watching

```bash
python src/workflow/document_workflow.py --watch --config config.yaml
```

Configure the directories to watch in config.yaml:

```yaml
watch_directories:
  - /path/to/watch/dir1
  - /path/to/watch/dir2
polling_interval: 300  # 5 minutes
```

### Batch Processing

For scheduled batch processing:

```bash
# Create a processing script
echo 'python src/cli.py ingest --path /path/to/new/documents --kb technical_docs' > process.sh
echo 'python src/cli.py chunk --kb technical_docs --all' >> process.sh
echo 'python src/cli.py map create --name "Updated Map" --kb technical_docs --all' >> process.sh
chmod +x process.sh

# Schedule with cron
crontab -e
# Add: 0 2 * * * /path/to/process.sh  # Run daily at 2 AM
```

## Best Practices

For optimal use of the Knowledge Management System:

### Document Organization

- **Consistent Structure**: Use consistent header patterns in markdown
- **Complete Documentation**: Include proper docstrings/comments in code
- **Logical Grouping**: Group related documents in directories

### Processing Strategy

- **Batch Size**: Process 20-50 documents at a time for best performance
- **Resource Planning**: Schedule large batch processing during off-hours
- **Regular Updates**: Process new documents regularly rather than in huge batches

### Citation Quality

- **Document Metadata**: Include author and version information when available
- **Structured Content**: Use clear headings in markdown documents
- **Code Documentation**: Include class and function documentation for better citations

### Knowledge Base Management

- **Multiple KBs**: Create separate knowledge bases for different domains
- **Regular Cleanup**: Archive or remove outdated documents
- **Documentation**: Create process documentation explaining the knowledge organization

### Search and Retrieval

- **Specific Queries**: Use specific terms for better results
- **Context Awareness**: Understand that chunks maintain document context
- **Citation Verification**: Always verify citations for critical information