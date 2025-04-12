# Knowledge Management System API Reference

This document provides a comprehensive reference for the Knowledge Management System's programmatic interfaces, including classes, methods, and REST API endpoints.

## Table of Contents

- [Core API](#core-api)
  - [KnowledgeSystem](#knowledgesystem)
  - [BulkIngestor](#bulkingestor)
  - [KnowledgeBaseRepository](#knowledgebaserepository)
  - [CitationProcessor](#citationprocessor)
  - [DocumentStore](#documentstore)
- [REST API](#rest-api)
  - [Knowledge Base Endpoints](#knowledge-base-endpoints)
  - [Document Endpoints](#document-endpoints)
  - [Processing Endpoints](#processing-endpoints)
  - [Search Endpoints](#search-endpoints)
- [Data Structures](#data-structures)
  - [Knowledge Base](#knowledge-base)
  - [Document Metadata](#document-metadata)
  - [Citation Information](#citation-information)
  - [Chunk Metadata](#chunk-metadata)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Examples](#examples)

## Core API

### KnowledgeSystem

The main entry point for interacting with the knowledge management system programmatically.

#### Constructor

```python
KnowledgeSystem(config=None)
```

- **config**: Optional configuration dictionary or path to config file

#### Methods

```python
ingest_document(file_path, metadata=None)
```

- **file_path**: Path to the document to ingest
- **metadata**: Optional dictionary of metadata for the document
- **Returns**: Document ID (string)

```python
search(query, user=None)
```

- **query**: Search query string
- **user**: Optional user information for access control
- **Returns**: List of search results with citation information

```python
generate_response(query, user=None)
```

- **query**: Question or prompt to answer using RAG
- **user**: Optional user information for access control
- **Returns**: Generated response with citations

### BulkIngestor

Processes multiple documents efficiently with resource management.

#### Constructor

```python
BulkIngestor(output_dir="/data/knowledge_base", kb_name=None, smart_ingestor=None, document_store=None, image_processor=None)
```

- **output_dir**: Base directory for processed files
- **kb_name**: Knowledge base name
- **smart_ingestor**: Optional SmartIngestor instance
- **document_store**: Optional DocumentStore instance
- **image_processor**: Optional image processor instance

#### Methods

```python
process_directory(input_dir)
```

- **input_dir**: Directory containing documents to process
- **Returns**: List of processed document IDs

```python
process_file(file_path)
```

- **file_path**: Path to the file to process
- **Returns**: Document ID

```python
chunk_document(doc_id, chunker)
```

- **doc_id**: Document ID to chunk
- **chunker**: SemanticChunker instance
- **Returns**: Number of chunks created

```python
generate_process_documentation(process_name, content, template=None)
```

- **process_name**: Name of the process
- **content**: Process documentation content
- **template**: Optional template for formatting
- **Returns**: Process documentation ID

```python
generate_knowledge_map(map_name, documents, relationships=None)
```

- **map_name**: Name of the knowledge map
- **documents**: List of document IDs to include
- **relationships**: Optional list of relationships between documents
- **Returns**: Map ID

### KnowledgeBaseRepository

Manages knowledge base repositories with Git integration.

#### Constructor

```python
KnowledgeBaseRepository(base_path="/data/knowledge_bases")
```

- **base_path**: Base directory for knowledge bases

#### Methods

```python
create_kb(kb_name, description="", owner="", metadata=None)
```

- **kb_name**: Name of the knowledge base
- **description**: Optional description
- **owner**: Optional owner information
- **metadata**: Optional additional metadata
- **Returns**: Path to the created knowledge base

```python
list_kbs()
```

- **Returns**: List of knowledge base information dictionaries

```python
get_kb(kb_name)
```

- **kb_name**: Name of the knowledge base
- **Returns**: Dictionary with KB info, path, and repo

```python
add_document(kb_name, doc_id, processed_path, metadata, citation=None)
```

- **kb_name**: Knowledge base name
- **doc_id**: Document ID
- **processed_path**: Path to processed document
- **metadata**: Document metadata
- **citation**: Optional citation information
- **Returns**: Path to the document in the KB

```python
add_chunks(kb_name, doc_id, chunks, chunk_metadata)
```

- **kb_name**: Knowledge base name
- **doc_id**: Document ID
- **chunks**: List of text chunks
- **chunk_metadata**: List of chunk metadata
- **Returns**: List of chunk file information

```python
update_documentation(kb_name, doc_type, name, content, commit_msg=None)
```

- **kb_name**: Knowledge base name
- **doc_type**: Documentation type ("process", "map", or "guide")
- **name**: Documentation name
- **content**: Documentation content
- **commit_msg**: Optional commit message
- **Returns**: Path to the documentation file

```python
clone_kb(kb_name, destination)
```

- **kb_name**: Knowledge base to clone
- **destination**: Destination path
- **Returns**: Path to the cloned KB

### CitationProcessor

Processes documents to create citation information.

#### Constructor

```python
CitationProcessor(output_dir="/data/knowledge_base")
```

- **output_dir**: Output directory for citation files

#### Methods

```python
process_document(document_path, doc_id, metadata)
```

- **document_path**: Path to the document
- **doc_id**: Document ID
- **metadata**: Document metadata
- **Returns**: Citation information dictionary

```python
generate_chunk_citations(chunks, doc_id)
```

- **chunks**: List of text chunks
- **doc_id**: Document ID
- **Returns**: List of citation information for chunks

### DocumentStore

Manages document storage across multiple backends.

#### Constructor

```python
DocumentStore(git_store=None, vector_store=None)
```

- **git_store**: Optional Git storage backend
- **vector_store**: Optional vector database backend

#### Methods

```python
store_document(document, metadata)
```

- **document**: Document content
- **metadata**: Document metadata
- **Returns**: Dictionary with storage IDs

```python
retrieve_document(doc_id)
```

- **doc_id**: Document ID
- **Returns**: Document content

## REST API

The web interface exposes a REST API for integration.

### Knowledge Base Endpoints

#### GET /api/kbs

Lists all knowledge bases.

**Response**:
```json
[
  {
    "name": "technical_docs",
    "description": "Technical Documentation",
    "created_at": "2025-04-12T10:30:00.000Z",
    "owner": "John Doe",
    "uuid": "123e4567-e89b-12d3-a456-426614174000"
  }
]
```

#### POST /api/kbs

Creates a new knowledge base.

**Request**:
```json
{
  "name": "api_docs",
  "description": "API Documentation",
  "owner": "Jane Smith"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Knowledge base api_docs created successfully",
  "path": "/data/knowledge_bases/api_docs"
}
```

#### GET /api/kbs/{kb_name}/status

Gets the status of a knowledge base.

**Response**:
```json
{
  "name": "technical_docs",
  "description": "Technical Documentation",
  "created_at": "2025-04-12T10:30:00.000Z",
  "owner": "John Doe",
  "path": "/data/knowledge_bases/technical_docs",
  "stats": {
    "raw_files": 120,
    "processed_files": 120,
    "metadata_files": 120,
    "citation_files": 120,
    "chunks": 543,
    "documentation": 5
  }
}
```

### Document Endpoints

#### POST /api/upload

Uploads and processes documents.

**Form Data**:
- `kb_name`: Knowledge base name
- `files`: Document files (multipart/form-data)

**Response**:
```json
{
  "status": "success",
  "message": "Upload successful, processing 10 files",
  "task_id": "123e4567-e89b-12d3-a456-426614174001",
  "batch_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

### Processing Endpoints

#### GET /api/tasks/{task_id}

Gets the status of a processing task.

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "type": "process_batch",
  "status": "processing",
  "kb_name": "technical_docs",
  "created_at": "2025-04-12T10:45:00.000Z",
  "progress": 45,
  "files": ["/tmp/uploads/file1.pdf", "/tmp/uploads/file2.md"]
}
```

#### GET /api/tasks

Gets all active and completed tasks.

**Response**:
```json
{
  "active": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "type": "process_batch",
      "status": "processing",
      "kb_name": "technical_docs",
      "progress": 45
    }
  ],
  "completed": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "type": "chunk_documents",
      "status": "completed",
      "kb_name": "technical_docs",
      "progress": 100,
      "result": {
        "total_documents": 5,
        "total_chunks": 25
      }
    }
  ]
}
```

#### POST /api/create_maps

Creates knowledge maps for documents.

**Request**:
```json
{
  "kb_name": "technical_docs",
  "doc_ids": ["doc1", "doc2", "doc3"]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Creating maps for 3 documents",
  "task_id": "123e4567-e89b-12d3-a456-426614174004"
}
```

#### POST /api/chunk_documents

Chunks documents for RAG.

**Request**:
```json
{
  "kb_name": "technical_docs",
  "doc_ids": ["doc1", "doc2", "doc3"],
  "max_tokens": 512,
  "overlap": 64
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Chunking 3 documents",
  "task_id": "123e4567-e89b-12d3-a456-426614174005"
}
```

#### POST /api/process_workflow

Executes a complete processing workflow.

**Form Data**:
- `kb_name`: Knowledge base name
- `files`: Document files (multipart/form-data)

**Response**:
```json
{
  "status": "success",
  "message": "Started workflow for 10 files",
  "workflow_id": "123e4567-e89b-12d3-a456-426614174006",
  "batch_id": "123e4567-e89b-12d3-a456-426614174007"
}
```

### Search Endpoints

#### GET /api/search?kb={kb_name}&query={query}

Searches the knowledge base.

**Query Parameters**:
- `kb`: Knowledge base name
- `query`: Search query
- `limit` (optional): Maximum number of results (default: 10)

**Response**:
```json
[
  {
    "chunk_id": "doc1_chunk_5",
    "doc_id": "doc1",
    "title": "Authentication API",
    "snippet": "The authentication system uses OAuth 2.0 with JWT tokens...",
    "citation": "Authentication API, Section: Authentication Flow, Lines 25-32",
    "score": 0.89
  },
  {
    "chunk_id": "doc2_chunk_12",
    "doc_id": "doc2",
    "title": "Security Guide",
    "snippet": "Token validation should be performed on all protected endpoints...",
    "citation": "Security Guide, Section: API Security, Lines 45-50",
    "score": 0.76
  }
]
```

## Data Structures

### Knowledge Base

```json
{
  "name": "string",
  "description": "string",
  "created_at": "ISO timestamp",
  "owner": "string",
  "uuid": "string",
  "path": "string"
}
```

### Document Metadata

```json
{
  "doc_id": "string",
  "title": "string",
  "filename": "string",
  "original_path": "string",
  "file_type": "string",
  "content_type": "string",
  "creation_time": "ISO timestamp",
  "modification_time": "ISO timestamp",
  "file_size": "number",
  "processing_time": "ISO timestamp",
  "knowledge_base": "string",
  "version": "string",
  "language": "string (optional)",
  "line_count": "number (optional)",
  "functions": ["string"] (optional),
  "classes": ["string"] (optional)
}
```

### Citation Information

```json
{
  "doc_id": "string",
  "filename": "string",
  "title": "string",
  "path": "string",
  "created_at": "ISO timestamp",
  "processed_at": "ISO timestamp",
  "content_type": "string",
  "file_type": "string",
  "author": "string",
  "version": "string",
  "repository": "string",
  "citation_format": "string",
  "sections": [
    {
      "type": "string",
      "name": "string",
      "start_line": "number (optional)",
      "end_line": "number (optional)",
      "page_number": "number (optional)",
      "content_hash": "string (optional)",
      "citation_key": "string"
    }
  ]
}
```

### Chunk Metadata

```json
{
  "chunk_id": "string",
  "doc_id": "string",
  "title": "string",
  "author": "string",
  "version": "string",
  "sections": [
    {
      "type": "string",
      "name": "string",
      "citation_key": "string",
      "start_line": "number (optional)",
      "end_line": "number (optional)"
    }
  ],
  "citation_text": "string",
  "repository_link": "string"
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- **200**: Success
- **400**: Bad request (missing or invalid parameters)
- **404**: Resource not found
- **500**: Server error

Error responses include an error message:

```json
{
  "error": "Error message description"
}
```

## Authentication

*Note: Authentication is not implemented in the current version but is planned for future releases.*

The API will support token-based authentication:

```
Authorization: Bearer <token>
```

## Examples

### Processing Documents Programmatically

```python
from src.main import KnowledgeSystem
from src.ingestor.bulk_ingestor import BulkIngestor
from src.processor.kb_repository import KnowledgeBaseRepository

# Create a knowledge base
kb_repo = KnowledgeBaseRepository()
kb_path = kb_repo.create_kb("api_docs", "API Documentation", "John Doe")

# Process a directory of documents
ingestor = BulkIngestor(kb_name="api_docs")
doc_ids = ingestor.process_directory("/path/to/documents")
print(f"Processed {len(doc_ids)} documents")

# Create knowledge map
ingestor.generate_knowledge_map("API Documentation Map", doc_ids)

# Process a specific file
doc_id = ingestor.process_file("/path/to/specific/file.md")
print(f"Processed document: {doc_id}")

# Chunk documents
from src.processor.chunker import SemanticChunker
chunker = SemanticChunker()
for doc_id in doc_ids:
    chunk_count = ingestor.chunk_document(doc_id, chunker)
    print(f"Created {chunk_count} chunks for document {doc_id}")
```

### Searching and RAG

```python
from src.main import KnowledgeSystem

# Initialize the system
system = KnowledgeSystem()

# Search the knowledge base
results = system.search("authentication process", 
                        user={"id": "user123", "role": "developer"})
for result in results:
    print(f"Result: {result['title']}")
    print(f"Citation: {result['citation']}")
    print(f"Snippet: {result['snippet']}")
    print("-" * 50)

# Generate a response with RAG
response = system.generate_response("How does the authentication system work?")
print(response)
```

### Using the REST API with curl

```bash
# Create a knowledge base
curl -X POST http://localhost:5000/api/kbs \
  -H "Content-Type: application/json" \
  -d '{"name":"api_docs","description":"API Documentation","owner":"Jane Smith"}'

# Upload documents
curl -X POST http://localhost:5000/api/upload \
  -F "kb_name=api_docs" \
  -F "files=@/path/to/document1.pdf" \
  -F "files=@/path/to/document2.md"

# Check task status
curl -X GET http://localhost:5000/api/tasks/task_id_from_previous_response

# Search the knowledge base
curl -X GET "http://localhost:5000/api/search?kb=api_docs&query=authentication&limit=5"
```