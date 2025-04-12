# Knowledge Management System Configuration Guide

This guide explains how to configure the Knowledge Management System for your organization's specific needs.

## Configuration Files

The system uses a flexible configuration approach with multiple sources:

1. **Default Configuration**: Built-in defaults for all settings
2. **Configuration File**: A YAML file with your custom settings
3. **Environment Variables**: Override settings with environment variables
4. **Command-line Arguments**: Override specific settings via command line

## Configuration File

The primary way to configure the system is through a YAML configuration file. 

### File Locations

The system looks for configuration files in the following locations (in order):

1. Path specified via command line: `--config /path/to/config.yaml`
2. Current directory: `./config.yaml`
3. Configuration directory: `./conf/config.yaml`
4. System-wide configuration: `/etc/knowledge-system/config.yaml`
5. User home directory: `~/.config/knowledge-system/config.yaml` or `~/.knowledge-system/config.yaml`

### Creating a Configuration File

Start by copying the example configuration file:

```bash
cp config.yaml.example config.yaml
```

Then edit the file to match your requirements.

## Configuration Sections

### Base Paths

```yaml
# Base paths - Configure these for your environment
output_dir: /data/knowledge_base
kb_base_dir: /data/knowledge_bases  
temp_dir: /tmp/kb_uploads
```

* `output_dir`: Main output directory for the knowledge base
* `kb_base_dir`: Base directory for all knowledge base repositories
* `temp_dir`: Temporary directory for uploads and processing

### Company Information

```yaml
# Company information - Customize with your company details
company:
  name: "Acme Corporation"
  logo_url: "/path/to/logo.png"  # Path or URL to company logo
  color_primary: "#1976D2"        # Primary brand color
  color_secondary: "#F57C00"      # Secondary brand color
  domain: "acme.example.com"
  contact_email: "support@acme.example.com"
```

These settings customize the UI and generated documents with your company branding.

### Web UI Configuration

```yaml
# Web UI configuration
web_ui:
  enabled: true
  host: 0.0.0.0
  port: 5000
  debug: false
  title: "Acme Knowledge Management System"
  session_secret: "change-this-in-production-env"  # IMPORTANT: Set this in production
  max_upload_size_mb: 1024  # 1GB
  allowed_file_types:
    - .py
    - .js
    - .md
    # ... more file extensions
```

* `enabled`: Enable/disable the web interface
* `host`: Host to bind the web server to (0.0.0.0 for all interfaces)
* `port`: Port to listen on
* `debug`: Enable debug mode (for development only)
* `title`: Title displayed in the web interface
* `session_secret`: Secret key for session encryption (IMPORTANT: change this in production)
* `max_upload_size_mb`: Maximum upload size in megabytes
* `allowed_file_types`: List of file extensions allowed for upload

### API Configuration

```yaml
# API configuration
api:
  enabled: true
  require_auth: true
  auth_provider: "jwt"  # "none", "jwt", "oauth2"
  jwt_secret: "change-this-in-production-env"  # IMPORTANT: Set this in production
  token_expiry_hours: 24
  rate_limit:
    enabled: true
    requests_per_minute: 60
  cors:
    enabled: true
    allow_origins: 
      - "https://acme.example.com"
    allow_methods:
      - "GET"
      - "POST"
      - "PUT"
      - "DELETE"
```

* `enabled`: Enable/disable the API
* `require_auth`: Require authentication for API access
* `auth_provider`: Authentication provider to use
* `jwt_secret`: Secret key for JWT token encryption (IMPORTANT: change this in production)
* `token_expiry_hours`: Token expiry time in hours
* `rate_limit`: API rate limiting settings
* `cors`: Cross-Origin Resource Sharing settings

### Processing Configuration

```yaml
# Document processing configuration
processing:
  batch_size: 50               # Number of documents to process in one batch
  polling_interval: 300        # Directory watch interval in seconds (5 minutes)
  max_workers: 4               # Maximum concurrent worker threads
  chunk_size: 10               # Process files in chunks of 10
  memory_limit_mb: 1024        # 1GB memory limit (soft limit)
  git_auto_commit: true        # Automatically commit changes to Git
```

* `batch_size`: Number of documents to process in one batch
* `polling_interval`: Interval for checking watched directories (in seconds)
* `max_workers`: Maximum number of concurrent worker threads
* `chunk_size`: Number of files to process in one chunk
* `memory_limit_mb`: Memory limit for processing (in megabytes)
* `git_auto_commit`: Automatically commit changes to Git after processing

### Chunking Configuration

```yaml
# Chunking configuration
chunking:
  max_tokens: 512              # Maximum tokens per chunk
  overlap: 64                  # Overlap between chunks
  min_chunk_size: 100          # Minimum characters per chunk
  respect_boundaries: true     # Respect semantic boundaries
```

* `max_tokens`: Maximum number of tokens per chunk
* `overlap`: Number of tokens to overlap between chunks
* `min_chunk_size`: Minimum size of a chunk (in characters)
* `respect_boundaries`: Respect semantic boundaries when chunking

### Storage Configuration

```yaml
# Storage configuration
storage:
  vector_store:
    type: "faiss"             # "faiss", "qdrant", "elastic"
    path: "/data/knowledge_base/vectors"
    dimensions: 768
    metric: "cosine"
  git_store:
    enabled: true
    lfs_enabled: false        # Git LFS for large files
    auto_push: false          # Auto push to remote
    remote_url: null
    username: null            # Leave as null if using SSH keys
    token: null               # GitHub/GitLab token if needed
```

* `vector_store`: Vector database configuration
* `git_store`: Git repository configuration

### Image Processing

```yaml
# Image processing
image_processing:
  enabled: true
  ocr: true
  ocr_engine: "tesseract"     # "tesseract", "google", "azure"
  ocr_api_key: null           # API key for cloud OCR services
  image_description: true     # Generate descriptions for images
```

* `enabled`: Enable/disable image processing
* `ocr`: Enable/disable OCR for images
* `ocr_engine`: OCR engine to use
* `ocr_api_key`: API key for cloud OCR services
* `image_description`: Generate descriptions for images

### Search Configuration

```yaml
# Search configuration
search:
  hybrid_search: true         # Combine vector and keyword search
  vector_weight: 0.7
  keyword_weight: 0.3
  max_results: 10
  min_score: 0.5              # Minimum similarity score (0-1)
```

* `hybrid_search`: Enable/disable hybrid search (vector + keyword)
* `vector_weight`: Weight for vector search in hybrid search
* `keyword_weight`: Weight for keyword search in hybrid search
* `max_results`: Maximum number of search results to return
* `min_score`: Minimum similarity score for search results

### Security Configuration

```yaml
# Security configuration
security:
  abac_enabled: false         # Attribute-based access control
  audit_trail: true           # Log all access
  pii_detection: false        # Personally identifiable information detection
  sensitive_info_detection: false  # Detect sensitive information
```

* `abac_enabled`: Enable/disable attribute-based access control
* `audit_trail`: Enable/disable audit trail
* `pii_detection`: Enable/disable PII detection
* `sensitive_info_detection`: Enable/disable sensitive information detection

### Logging Configuration

```yaml
# Logging configuration
logging:
  level: "INFO"               # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "knowledge_system.log"
  max_size_mb: 10
  backup_count: 3
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

* `level`: Logging level
* `file`: Log file path
* `max_size_mb`: Maximum log file size (in megabytes)
* `backup_count`: Number of backup log files to keep
* `format`: Log message format

### Watch Directories

```yaml
# Watch directories for automated processing
watch_directories:
  - "/path/to/watch/dir1"
  - "/path/to/watch/dir2"
```

List of directories to monitor for new files to process automatically.

## Environment Variables

You can override configuration settings using environment variables with the prefix `KB_`.

Environment variable names are derived from the configuration keys by:
1. Adding the `KB_` prefix
2. Converting to uppercase
3. Replacing dots with underscores

For example, to set the `web_ui.port` configuration:

```bash
export KB_WEB_UI_PORT=8080
```

For nested configuration, use underscores:

```bash
export KB_COMPANY_NAME="My Company"
export KB_PROCESSING_MAX_WORKERS=8
```

## Command-line Arguments

Some components accept command-line arguments that override configuration file settings.

For example, with the CLI:

```bash
python src/cli.py ingest --path /path/to/documents --kb technical_docs --config custom_config.yaml
```

## Secure Production Configuration

For production deployments, ensure you:

1. Set secure values for `web_ui.session_secret` and `api.jwt_secret`
2. Enable authentication for API access (`api.require_auth: true`)
3. Set appropriate CORS origins (`api.cors.allow_origins`)
4. Use HTTPS for all external access
5. Set appropriate file permissions on configuration files
6. Consider enabling ABAC for fine-grained access control

## Example: Development Configuration

```yaml
output_dir: ./data/knowledge_base
kb_base_dir: ./data/knowledge_bases
temp_dir: ./tmp/uploads

web_ui:
  debug: true
  port: 8080

processing:
  max_workers: 2
  memory_limit_mb: 512

logging:
  level: "DEBUG"
```

## Example: Production Configuration

```yaml
output_dir: /data/knowledge_base
kb_base_dir: /data/knowledge_bases
temp_dir: /tmp/kb_uploads

company:
  name: "Enterprise Solutions Ltd."
  logo_url: "/var/www/assets/logo.png"
  domain: "enterprise-kb.example.com"

web_ui:
  debug: false
  port: 5000
  session_secret: "YOUR-SECURE-SESSION-SECRET"
  
api:
  require_auth: true
  auth_provider: "jwt"
  jwt_secret: "YOUR-SECURE-JWT-SECRET"
  cors:
    allow_origins: 
      - "https://enterprise-kb.example.com"
      - "https://app.example.com"

processing:
  max_workers: 8
  memory_limit_mb: 4096

security:
  abac_enabled: true
  audit_trail: true

logging:
  level: "INFO"
  file: "/var/log/knowledge_system.log"
```

## Validation

The system validates your configuration at startup and will:
1. Log warnings for missing recommended settings
2. Create required directories automatically
3. Fall back to defaults for any missing settings
4. Validate critical settings and fail with clear error messages if they are invalid