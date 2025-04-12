# Knowledge Management System Architecture

This document outlines the architectural design, components, and data flow of the Knowledge Management System.

## System Overview

The Knowledge Management System is designed to transform static documents into dynamic, interconnected knowledge assets with robust citation information and RAG compatibility. The architecture prioritizes:

- **Document integrity**: Preserving original documents while enhancing their structure
- **Citation traceability**: Maintaining precise location information for all knowledge chunks
- **Resource efficiency**: Processing large document volumes with controlled resource usage
- **Knowledge organization**: Creating meaningful structure and relationships
- **RAG optimization**: Preparing content for effective retrieval-augmented generation

## Architecture Diagram

```
┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
│                    │         │                    │         │                    │
│   Input Sources    │─────────▶  Processing Layer  │─────────▶  Storage Layer     │
│                    │         │                    │         │                    │
└────────────────────┘         └────────────────────┘         └────────────────────┘
          │                              │                             │
          │                              │                             │
          ▼                              ▼                             ▼
┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
│  - Documents       │         │  - Extraction      │         │  - Git Repository  │
│  - Code Files      │         │  - Transformation  │         │  - Vector Database │
│  - Markdown        │         │  - Chunking        │         │  - File System     │
│  - Images          │         │  - Citation        │         │  - Metadata Store  │
└────────────────────┘         └────────────────────┘         └────────────────────┘
                                                                       │
                                                                       │
          ┌─────────────────────────────────────────────────────────────┐
          │                                                             │
          ▼                                                             ▼
┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
│                    │         │                    │         │                    │
│   Access Layer     │◀────────▶   Interface Layer  │◀────────▶  Integration Layer │
│                    │         │                    │         │                    │
└────────────────────┘         └────────────────────┘         └────────────────────┘
          │                              │                             │
          │                              │                             │
          ▼                              ▼                             ▼
┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
│  - Search Engine   │         │  - CLI Tools       │         │  - API             │
│  - RAG System      │         │  - Web Interface   │         │  - LLM Integration │
│  - Security/ABAC   │         │  - Workflow Tools  │         │  - Export/Import   │
└────────────────────┘         └────────────────────┘         └────────────────────┘
```

## Core Components

### 1. Input Layer

**BulkIngestor**: Processes directories of documents, handling various file types.
- Manages document traversal and discovery
- Routes documents to appropriate handlers
- Creates initial metadata

**SmartIngestor**: Handles specific document formats with specialized processing.
- PDF handler with OCR capabilities
- Code file parser with structure extraction
- Markdown processor with image handling

**SimpleImageProcessor**: Extracts text information from images.
- OCR processing for images
- Alt text extraction from embedded images
- Image description generation

### 2. Processing Layer

**CitationProcessor**: Creates citation information for each document.
- Processes document structure to identify citable elements
- Creates unique citation keys for document sections
- Maps chunks to their citation information

**SemanticChunker**: Divides documents into meaningful chunks for RAG.
- Creates semantically cohesive chunks
- Maintains document structure during chunking
- Preserves context across chunk boundaries
- Applies overlap to ensure concept continuity

**VectorOptimizer**: Prepares text for embedding.
- Cleans text to improve embedding quality
- Processes text for optimal vector representation
- Maintains citation links during transformation

### 3. Storage Layer

**KnowledgeBaseRepository**: Manages knowledge base repositories with Git integration.
- Creates standardized KB structure
- Handles document organization
- Commits changes to Git
- Manages version control

**DocumentStore**: Handles document storage across multiple backends.
- Git-based storage for document versioning
- Vector database interface for embeddings
- Manages document retrieval and updates

### 4. Access Layer

**HybridSearch**: Combines vector and keyword search for optimal results.
- Performs vector similarity search
- Enhances with keyword matching
- Ranks results by relevance
- Preserves citation information

**RAGSystem**: Implements retrieval-augmented generation.
- Retrieves relevant documents
- Augments prompts with context
- Generates responses with citations
- Manages context windows

**ABACEngine**: Implements attribute-based access control.
- Controls access to documents
- Enforces security policies
- Maintains audit trail

### 5. Interface Layer

**CLI Interface**: Command-line tools for system interaction.
- Document ingestion commands
- KB management tools
- Search and retrieval interfaces
- Process management

**Web Interface**: Browser-based UI for system management.
- Document upload and processing
- KB status monitoring
- Task management
- Search interface

**DocumentWorkflow**: Tools for automating document processing.
- Directory watching
- Batch processing
- Workflow tracking
- Process documentation

### 6. Integration Layer

**API**: Programmatic interface for system integration.
- Document ingestion endpoints
- Search and retrieval methods
- KB management functions
- Authentication and security

## Data Flow

### Document Processing Flow

1. **Input**: Documents enter the system via BulkIngestor or Web UI
2. **Format Detection**: SmartIngestor identifies document type
3. **Content Extraction**: Format-specific handlers extract content
4. **Structure Analysis**: System identifies document structure
5. **Metadata Creation**: Metadata is extracted and stored
6. **Citation Generation**: CitationProcessor creates citation information
7. **Document Storage**: Processed document is stored in KB repository
8. **Chunking**: SemanticChunker divides document for RAG
9. **Vector Generation**: Chunks are converted to vector representations
10. **Indexing**: Vectors and text are indexed for search

### Search and Retrieval Flow

1. **Query Input**: User enters search query
2. **Query Processing**: System analyzes query intent
3. **Vector Search**: Query is converted to vector and searched
4. **Keyword Enhancement**: Results are enhanced with keyword matching
5. **Citation Retrieval**: Citation information is attached to results
6. **Result Ranking**: Results are ranked by relevance
7. **Response Generation**: For RAG, context is used to generate response
8. **Citation Inclusion**: Citations are included in final results

## Data Model

### Knowledge Base

The core data structure organizing all content:

```
KnowledgeBase {
  name: string
  description: string
  created_at: timestamp
  owner: string
  uuid: string
  path: string
}
```

### Document Metadata

Each document has associated metadata:

```
DocumentMetadata {
  doc_id: string
  title: string
  filename: string
  original_path: string
  file_type: string
  content_type: string
  creation_time: timestamp
  modification_time: timestamp
  file_size: number
  processing_time: timestamp
  knowledge_base: string
  version: string
  language?: string  // For code files
  line_count?: number  // For code files
  functions?: string[]  // For code files
  classes?: string[]  // For code files
}
```

### Citation Information

Citation data tracks precise source information:

```
Citation {
  doc_id: string
  filename: string
  title: string
  path: string
  created_at: timestamp
  processed_at: timestamp
  content_type: string
  file_type: string
  author: string
  version: string
  repository: string
  citation_format: string
  sections: [
    {
      type: string  // "class", "function", "header", "page", etc.
      name: string
      start_line?: number
      end_line?: number
      page_number?: number
      content_hash?: string
      citation_key: string
    }
  ]
}
```

### Chunk Metadata

Each chunk maintains its provenance:

```
ChunkMetadata {
  chunk_id: string
  doc_id: string
  title: string
  author: string
  version: string
  sections: [
    {
      type: string
      name: string
      citation_key: string
      start_line?: number
      end_line?: number
    }
  ]
  citation_text: string
  repository_link: string
}
```

## Key Technologies

- **Python**: Core implementation language
- **Git**: Version control and document storage
- **Flask**: Web interface framework
- **FAISS/Qdrant**: Vector database options
- **SpaCy**: NLP processing (potential future integration)
- **Tesseract OCR**: Image text extraction
- **Markdown**: Standard document format

## Design Principles

### 1. Resource Efficiency

The system is designed to handle large document volumes with controlled resource usage:

- **Batch Processing**: Documents are processed in configurable batches
- **Memory Management**: Resources are released between processing steps
- **Concurrent Processing**: Multi-threading with controlled worker pools
- **Resource Limits**: Configurable limits on CPU and memory usage

### 2. Citation Integrity

Every piece of information maintains its provenance:

- **Document Linking**: Each chunk links to its source document
- **Location Precision**: Code functions, markdown sections, PDF pages
- **Version Tracking**: Document versions are tracked
- **Canonical References**: PDF/text versions for stable referencing

### 3. Knowledge Organization

Content is meaningfully organized:

- **Repository Structure**: Standardized KB repository layout
- **Document Grouping**: Content is categorized by type and subject
- **Knowledge Maps**: Visual and structural relationships
- **Process Documentation**: Workflows and procedures are documented

### 4. Extensibility

The system is designed for extension:

- **Pluggable Components**: Handlers can be added for new document types
- **Configuration Options**: Behavior can be customized through configuration
- **API Integration**: Programmatic access for integration

## Performance Considerations

### Scalability

- **Document Volume**: System handles 100+ documents per batch
- **Repository Size**: Each KB can manage thousands of documents
- **Vector Database**: Scales to millions of chunks

### Resource Usage

- **Memory Control**: Batch processing to limit peak memory
- **CPU Management**: Worker pool with controlled concurrency
- **Disk Usage**: Git LFS for large files, efficient storage

### Optimization Strategies

- **Chunking Parameters**: Configurable chunk size and overlap
- **Vector Dimensions**: Optimized embedding dimensions for balance
- **Processing Priorities**: Most important documents processed first

## Security Considerations

- **Access Control**: ABAC engine for controlled access
- **Audit Trail**: All document access is logged
- **Authentication**: Integration with external auth systems
- **Data Protection**: Sensitive information handling

## Future Extensions

- **Multi-Modal Processing**: Enhanced image and diagram understanding
- **Custom Embedding Models**: Domain-specific vector embeddings
- **Real-Time Collaboration**: Collaborative knowledge management
- **Advanced Knowledge Maps**: AI-generated relationship mapping
- **Semantic Search Improvements**: Enhanced query understanding