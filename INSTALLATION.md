# Knowledge Management System Installation Guide

This guide provides detailed step-by-step instructions for installing and running the Knowledge Management System.

## System Requirements

- Python 3.8+ (3.9 or 3.10 recommended)
- Git 2.20+ with Git LFS
- 4GB+ RAM recommended
- 1GB+ of free disk space
- Linux, macOS, or Windows with WSL

## Step 1: Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/knowledge-mgmt-system.git
cd knowledge-mgmt-system
```

## Step 2: Create and Activate a Virtual Environment

Create a Python virtual environment to isolate dependencies:

### On Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

### On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

## Step 3: Install Dependencies

Install all required dependencies:

```bash
pip install -r src/requirements.txt
```

For OCR support (optional but recommended):

### On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

### On macOS:

```bash
brew install tesseract
```

### On Windows:

Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

## Step 4: Configure the System

Create a configuration file at `config.yaml` in the root directory:

```bash
touch config.yaml
```

Edit the file with your preferred settings:

```yaml
# Basic Configuration
output_dir: /data/knowledge_base
kb_base_dir: /data/knowledge_bases

# Document Processing
chunking:
  max_tokens: 512
  overlap: 64

# Storage Configuration
vector_store:
  type: faiss
  path: /data/knowledge_base/vectors

# Git Configuration  
git_store:
  enabled: true

# Processing Options
batch_size: 50
polling_interval: 300  # 5 minutes

# Image Processing
image_processing:
  enabled: true
  ocr: true
```

**Important**: Make sure the directories in your configuration exist:

```bash
mkdir -p /data/knowledge_base
mkdir -p /data/knowledge_bases
```

## Step 5: Test the Installation

Run a quick test to ensure everything is working:

```bash
cd knowledge-mgmt-system
python -c "from src.main import KnowledgeSystem; system = KnowledgeSystem(); print('Installation successful!')"
```

If you see "Installation successful!" the core system is working correctly.

## Running the System

There are three main ways to use the system:

### 1. Command Line Interface (CLI)

The CLI provides command-line tools for managing knowledge bases:

```bash
# Create a knowledge base
python src/cli.py kb create --name technical_docs --description "Technical Documentation" --owner "Your Name"

# List knowledge bases
python src/cli.py kb list

# Check status of a knowledge base
python src/cli.py kb status --name technical_docs

# Ingest documents
python src/cli.py ingest --path /path/to/documents --kb technical_docs

# Chunk documents for RAG
python src/cli.py chunk --kb technical_docs --all

# Search knowledge base
python src/cli.py search "search query" --kb technical_docs
```

### 2. Web Interface

The web interface provides a user-friendly way to manage and use knowledge bases:

```bash
# Start the web server
python src/ui/app.py
```

Then open your browser to: http://localhost:5000

The web interface allows you to:
- Create and manage knowledge bases
- Upload and process documents in bulk
- Generate knowledge maps and process documentation
- Monitor processing tasks
- Search knowledge bases

### 3. API Usage

You can use the system programmatically:

```python
from src.main import KnowledgeSystem
from src.ingestor.bulk_ingestor import BulkIngestor
from src.processor.kb_repository import KnowledgeBaseRepository

# Initialize the system
system = KnowledgeSystem()

# Create a knowledge base
kb_repo = KnowledgeBaseRepository()
kb_repo.create_kb("api_docs", "API Documentation", "Your Name")

# Process a document
doc_id = system.ingest_document("/path/to/document.pdf", {"type": "api"})

# Search for information
results = system.search("authentication", user={"id": "user123"})

# Generate a response using RAG
response = system.generate_response("How does the authentication system work?")
print(response)
```

## Processing Large Document Volumes

For bulk document processing, use either:

### Command Line Approach:

```bash
# Process an entire directory
python src/cli.py ingest --path /path/to/large/document/directory --kb your_kb_name

# Create knowledge maps for all documents
python src/cli.py map create --name "All Documents" --kb your_kb_name --all

# Chunk all documents for RAG
python src/cli.py chunk --kb your_kb_name --all
```

### Web Interface Approach (Recommended for Large Volumes):

1. Start the web server: `python src/ui/app.py`
2. Go to http://localhost:5000 in your browser
3. Navigate to the "Upload" tab
4. Select your knowledge base from the dropdown
5. Drag and drop all your documents (up to 100 at once)
6. Click "Upload and Process Documents"
7. Monitor the progress on the Tasks tab

## Monitoring and Management

### Check Knowledge Base Status

```bash
python src/cli.py kb status --name your_kb_name
```

This will show:
- Number of documents
- Citation files
- Chunks
- Documentation

### View Knowledge Base Directory

Each knowledge base is stored as a Git repository in your configured `kb_base_dir`:

```bash
ls -la /data/knowledge_bases/your_kb_name
```

The structure will be:
- `raw/`: Original documents
- `processed/`: Processed markdown versions
- `metadata/`: Document metadata
- `citations/`: Citation information
- `chunks/`: Chunked content for RAG
- `vectors/`: Vector embeddings
- `workflows/`: Processing workflow records
- `pdfs/`: PDF versions for citation
- `documentation/`: KB documentation

## Troubleshooting

### Common Issues

1. **Missing Directories**:
   ```
   Error: Directory not found: /data/knowledge_bases
   ```
   
   Solution: Create the required directories
   ```bash
   mkdir -p /data/knowledge_base /data/knowledge_bases
   ```

2. **Memory Issues with Large Documents**:
   
   Solution: Adjust batch size in your config.yaml file
   ```yaml
   batch_size: 20  # Lower this value
   ```

3. **Slow Processing**:
   
   Solution: Adjust worker thread count in src/ui/app.py
   ```python
   app.config['RESOURCE_LIMITS'] = {
       'max_workers': 2,  # Reduce if CPU usage is too high
       'chunk_size': 5,   # Process fewer files simultaneously
   }
   ```

4. **Web UI Not Starting**:
   
   Solution: Check port availability
   ```bash
   # Check if port 5000 is in use
   lsof -i :5000
   
   # Start UI on a different port
   PORT=5001 python src/ui/app.py
   ```

### Logs

Check the log files for detailed information:

- CLI log: `knowledge_system.log`
- UI log: `ui.log`

## Optimizing for Performance

For best performance with large document volumes:

1. **Hardware Recommendations**:
   - 8+ GB RAM
   - SSD storage
   - Multicore CPU (4+ cores recommended)

2. **Configuration Optimizations**:
   ```yaml
   # config.yaml optimizations
   batch_size: 30  # Adjust based on available memory
   chunking:
     max_tokens: 384  # Smaller chunks use less memory
     overlap: 32
   ```

3. **Web UI Resource Limits**:
   Edit src/ui/app.py to adjust resource usage:
   ```python
   app.config['RESOURCE_LIMITS'] = {
       'max_workers': 4,       # Maximum concurrent worker threads
       'chunk_size': 10,       # Process files in chunks of 10
       'memory_limit': 1024 * 1024 * 1024,  # 1GB memory limit
   }
   ```

## Advanced Usage

### Custom Document Processing

For specialized document formats, you can extend the `SmartIngestor` class:

1. Create a new file in `src/ingestor/custom_ingestor.py`
2. Implement a custom handler for your document type
3. Register it in the `SUPPORTED_FORMATS` dictionary

### Git Integration

Each knowledge base is a Git repository. You can use standard Git commands:

```bash
cd /data/knowledge_bases/your_kb_name
git log  # View commit history
git show # See latest changes
```

### Using the Vector Database Directly

For direct access to the vector database:

```python
from src.storage.document_store import DocumentStore

# Initialize document store
doc_store = DocumentStore()

# Get vector store
vector_store = doc_store.vector_store

# Perform a vector search
results = vector_store.search(query_vector, limit=10)
```

## Next Steps and Further Resources

After installation, read these additional documents:

1. `README.md` - Overview and features
2. `docs/API.md` - API documentation
3. `docs/CONCEPTS.md` - Core concepts

For questions and support, please open an issue on the GitHub repository.