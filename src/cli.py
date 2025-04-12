#!/usr/bin/env python3
import argparse
import sys
import os
from pathlib import Path
import yaml
import logging
from datetime import datetime

from ingestor.bulk_ingestor import BulkIngestor, SimpleImageProcessor
from ingestor.smart_ingestor import SmartIngestor
from storage.document_store import DocumentStore
from processor.chunker import SemanticChunker
from processor.vector_optimizer import VectorOptimizer
from processor.kb_repository import KnowledgeBaseRepository
from processor.citation_processor import CitationProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('knowledge_system.log')
    ]
)
logger = logging.getLogger('knowledge_cli')

def parse_args():
    parser = argparse.ArgumentParser(description='Knowledge Management System CLI')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest documents')
    ingest_parser.add_argument('--path', required=True, help='Path to directory or file to ingest')
    ingest_parser.add_argument('--output', default='/data/knowledge_base', 
                             help='Output directory for processed documents')
    ingest_parser.add_argument('--kb', default='default_kb', help='Knowledge base name')
    ingest_parser.add_argument('--config', help='Path to configuration file')
    ingest_parser.add_argument('--recursive', action='store_true', help='Process directories recursively')
    
    # KB command
    kb_parser = subparsers.add_parser('kb', help='Knowledge base management')
    kb_subparsers = kb_parser.add_subparsers(dest='kb_command', help='KB command')
    
    # KB create command
    kb_create_parser = kb_subparsers.add_parser('create', help='Create a new knowledge base')
    kb_create_parser.add_argument('--name', required=True, help='Knowledge base name')
    kb_create_parser.add_argument('--description', help='Knowledge base description')
    kb_create_parser.add_argument('--owner', help='Knowledge base owner')
    
    # KB list command
    kb_subparsers.add_parser('list', help='List knowledge bases')
    
    # KB status command
    kb_status_parser = kb_subparsers.add_parser('status', help='Show knowledge base status')
    kb_status_parser.add_argument('--name', required=True, help='Knowledge base name')
    
    # Process map command
    process_parser = subparsers.add_parser('process', help='Process documentation management')
    process_subparsers = process_parser.add_subparsers(dest='process_command', help='Process command')
    
    # Process create command
    process_create_parser = process_subparsers.add_parser('create', help='Create process documentation')
    process_create_parser.add_argument('--name', required=True, help='Process name')
    process_create_parser.add_argument('--content', required=True, help='Process content file path')
    process_create_parser.add_argument('--kb', required=True, help='Knowledge base name')
    
    # Map command
    map_parser = subparsers.add_parser('map', help='Knowledge map management')
    map_subparsers = map_parser.add_subparsers(dest='map_command', help='Map command')
    
    # Map create command
    map_create_parser = map_subparsers.add_parser('create', help='Create knowledge map')
    map_create_parser.add_argument('--name', required=True, help='Map name')
    map_create_parser.add_argument('--kb', required=True, help='Knowledge base name')
    map_create_parser.add_argument('--documents', help='File with list of document IDs')
    map_create_parser.add_argument('--all', action='store_true', help='Include all documents in KB')
    
    # Chunk command
    chunk_parser = subparsers.add_parser('chunk', help='Chunk documents')
    chunk_parser.add_argument('--kb', required=True, help='Knowledge base name')
    chunk_parser.add_argument('--doc-id', help='Document ID to chunk')
    chunk_parser.add_argument('--all', action='store_true', help='Chunk all documents in KB')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search the knowledge base')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--kb', required=True, help='Knowledge base name')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    
    # Version
    parser.add_argument('--version', action='store_true', help='Show version info')
    
    return parser.parse_args()

def load_config(config_path=None):
    """Load configuration from a YAML file."""
    default_config = {
        'output_dir': '/data/knowledge_base',
        'kb_base_dir': '/data/knowledge_bases',
        'chunking': {
            'max_tokens': 512,
            'overlap': 64
        },
        'vector_store': {
            'type': 'faiss',
            'path': '/data/knowledge_base/vectors'
        },
        'git_store': {
            'enabled': True
        },
        'image_processing': {
            'enabled': True,
            'ocr': True
        }
    }
    
    if not config_path:
        # Try to find config in default locations
        config_paths = [
            'config.yaml',
            'conf/config.yaml',
            os.path.expanduser('~/.knowledge-system/config.yaml'),
            '/etc/knowledge-system/config.yaml'
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge user config with default config
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                        
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    return default_config

def initialize_components(config, kb_name=None):
    """Initialize system components based on configuration."""
    
    # Initialize image processor if enabled
    image_processor = None
    if config.get('image_processing', {}).get('enabled', True):
        image_processor = SimpleImageProcessor()
    
    # Initialize document store
    document_store = DocumentStore()
    
    # Initialize smart ingestor
    smart_ingestor = SmartIngestor()
    
    # Initialize bulk ingestor
    bulk_ingestor = BulkIngestor(
        output_dir=config.get('output_dir', '/data/knowledge_base'),
        kb_name=kb_name,
        smart_ingestor=smart_ingestor,
        document_store=document_store,
        image_processor=image_processor
    )
    
    # Initialize KB repository
    kb_repo = KnowledgeBaseRepository(
        base_path=config.get('kb_base_dir', '/data/knowledge_bases')
    )
    
    # Initialize chunker
    chunker = SemanticChunker(
        max_tokens=config.get('chunking', {}).get('max_tokens', 512),
        overlap=config.get('chunking', {}).get('overlap', 64)
    )
    
    return {
        'bulk_ingestor': bulk_ingestor,
        'smart_ingestor': smart_ingestor,
        'document_store': document_store,
        'image_processor': image_processor,
        'kb_repo': kb_repo,
        'chunker': chunker
    }

def handle_ingest(args, config):
    """Handle the ingest command."""
    logger.info(f"Starting ingestion from {args.path}")
    
    components = initialize_components(config, args.kb)
    bulk_ingestor = components['bulk_ingestor']
    
    path = Path(args.path)
    
    if path.is_dir():
        # Process directory
        start_time = datetime.now()
        processed_files = bulk_ingestor.process_directory(path)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Processed {len(processed_files)} files in {duration:.2f} seconds")
        print(f"Successfully processed {len(processed_files)} files from {path}")
        print(f"Knowledge base: {bulk_ingestor.kb_name}")
        print(f"Output directory: {bulk_ingestor.output_dir}")
    elif path.is_file():
        # Process single file
        start_time = datetime.now()
        doc_id = bulk_ingestor.process_file(path)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Processed file {path} in {duration:.2f} seconds")
        print(f"Successfully processed file: {path}")
        print(f"Document ID: {doc_id}")
        print(f"Knowledge base: {bulk_ingestor.kb_name}")
        print(f"Output directory: {bulk_ingestor.output_dir}")
    else:
        logger.error(f"Invalid path: {path}")
        print(f"Error: Path not found: {path}")
        return 1
    
    return 0

def handle_kb_create(args, config):
    """Handle the KB create command."""
    components = initialize_components(config)
    kb_repo = components['kb_repo']
    
    try:
        kb_path = kb_repo.create_kb(
            args.name,
            description=args.description or f"Knowledge base created on {datetime.now().isoformat()}",
            owner=args.owner or "CLI user"
        )
        
        print(f"Successfully created knowledge base: {args.name}")
        print(f"Path: {kb_path}")
        return 0
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        print(f"Error: {e}")
        return 1

def handle_kb_list(args, config):
    """Handle the KB list command."""
    components = initialize_components(config)
    kb_repo = components['kb_repo']
    
    try:
        kbs = kb_repo.list_kbs()
        
        print(f"Found {len(kbs)} knowledge bases:")
        for kb in kbs:
            print(f"- {kb['name']}: {kb.get('description', 'No description')}")
            print(f"  Created: {kb.get('created_at', 'Unknown')}")
            print(f"  Owner: {kb.get('owner', 'Unknown')}")
            print()
            
        return 0
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {e}")
        print(f"Error: {e}")
        return 1

def handle_kb_status(args, config):
    """Handle the KB status command."""
    components = initialize_components(config)
    kb_repo = components['kb_repo']
    
    try:
        kb = kb_repo.get_kb(args.name)
        kb_path = kb['path']
        kb_info = kb['info']
        
        print(f"Knowledge Base: {kb_info['name']}")
        print(f"Description: {kb_info.get('description', 'No description')}")
        print(f"Created: {kb_info.get('created_at', 'Unknown')}")
        print(f"Owner: {kb_info.get('owner', 'Unknown')}")
        print(f"Path: {kb_path}")
        print()
        
        # Count files in directories
        def count_files(dir_path):
            if not dir_path.exists():
                return 0
            return sum(1 for _ in dir_path.glob("**/*") if _.is_file())
        
        print("Content Statistics:")
        print(f"- Raw files: {count_files(kb_path / 'raw')}")
        print(f"- Processed files: {count_files(kb_path / 'processed')}")
        print(f"- Metadata files: {count_files(kb_path / 'metadata')}")
        print(f"- Citation files: {count_files(kb_path / 'citations')}")
        print(f"- Chunks: {count_files(kb_path / 'chunks')}")
        print(f"- Documentation: {count_files(kb_path / 'documentation')}")
        
        return 0
    except Exception as e:
        logger.error(f"Error getting knowledge base status: {e}")
        print(f"Error: {e}")
        return 1

def handle_process_create(args, config):
    """Handle the process create command."""
    components = initialize_components(config, args.kb)
    bulk_ingestor = components['bulk_ingestor']
    
    try:
        # Read content file
        content_path = Path(args.content)
        if not content_path.exists():
            print(f"Error: Content file not found: {content_path}")
            return 1
            
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        process_name = bulk_ingestor.generate_process_documentation(
            args.name,
            content
        )
        
        print(f"Successfully created process documentation: {process_name}")
        print(f"Knowledge base: {bulk_ingestor.kb_name}")
        
        return 0
    except Exception as e:
        logger.error(f"Error creating process documentation: {e}")
        print(f"Error: {e}")
        return 1

def handle_map_create(args, config):
    """Handle the map create command."""
    components = initialize_components(config, args.kb)
    bulk_ingestor = components['bulk_ingestor']
    kb_repo = components['kb_repo']
    
    try:
        # Get documents
        documents = []
        
        if args.all:
            # Get all documents in KB
            kb = kb_repo.get_kb(args.kb)
            metadata_dir = kb['path'] / 'metadata'
            
            if metadata_dir.exists():
                for metadata_file in metadata_dir.glob("*.json"):
                    doc_id = metadata_file.stem
                    documents.append(doc_id)
        elif args.documents:
            # Read document list from file
            doc_list_path = Path(args.documents)
            if not doc_list_path.exists():
                print(f"Error: Document list file not found: {doc_list_path}")
                return 1
                
            with open(doc_list_path, 'r') as f:
                for line in f:
                    doc_id = line.strip()
                    if doc_id:
                        documents.append(doc_id)
        else:
            print("Error: Must specify --all or --documents")
            return 1
            
        if not documents:
            print("Error: No documents found")
            return 1
            
        # Create knowledge map
        map_name = bulk_ingestor.generate_knowledge_map(
            args.name,
            documents
        )
        
        print(f"Successfully created knowledge map: {map_name}")
        print(f"Knowledge base: {bulk_ingestor.kb_name}")
        print(f"Documents: {len(documents)}")
        
        return 0
    except Exception as e:
        logger.error(f"Error creating knowledge map: {e}")
        print(f"Error: {e}")
        return 1

def handle_chunk(args, config):
    """Handle the chunk command."""
    components = initialize_components(config, args.kb)
    bulk_ingestor = components['bulk_ingestor']
    chunker = components['chunker']
    kb_repo = components['kb_repo']
    
    try:
        # Get documents to chunk
        documents = []
        
        if args.doc_id:
            # Chunk specific document
            documents.append(args.doc_id)
        elif args.all:
            # Chunk all documents in KB
            kb = kb_repo.get_kb(args.kb)
            metadata_dir = kb['path'] / 'metadata'
            
            if metadata_dir.exists():
                for metadata_file in metadata_dir.glob("*.json"):
                    doc_id = metadata_file.stem
                    documents.append(doc_id)
        else:
            print("Error: Must specify --doc-id or --all")
            return 1
            
        if not documents:
            print("Error: No documents found")
            return 1
            
        # Chunk documents
        total_chunks = 0
        for doc_id in documents:
            try:
                chunk_count = bulk_ingestor.chunk_document(doc_id, chunker)
                total_chunks += chunk_count
                print(f"Chunked document {doc_id}: {chunk_count} chunks")
            except Exception as e:
                logger.error(f"Error chunking document {doc_id}: {e}")
                print(f"Error chunking document {doc_id}: {e}")
        
        print(f"Successfully chunked {len(documents)} documents into {total_chunks} chunks")
        print(f"Knowledge base: {bulk_ingestor.kb_name}")
        
        return 0
    except Exception as e:
        logger.error(f"Error chunking documents: {e}")
        print(f"Error: {e}")
        return 1

def handle_search(args, config):
    """Handle the search command."""
    print(f"Searching for '{args.query}' in knowledge base '{args.kb}'...")
    print("This feature is not yet fully implemented.")
    
    try:
        # Basic implementation to demonstrate
        components = initialize_components(config, args.kb)
        kb_repo = components['kb_repo']
        
        kb = kb_repo.get_kb(args.kb)
        chunks_dir = kb['path'] / 'chunks' / 'text'
        
        if not chunks_dir.exists():
            print("Error: No chunks found in knowledge base")
            return 1
            
        # Simple keyword search
        keyword = args.query.lower()
        found_chunks = []
        
        for chunk_file in chunks_dir.glob("*.txt"):
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if keyword in content:
                    chunk_id = chunk_file.stem
                    
                    # Get chunk metadata
                    metadata_file = kb['path'] / 'chunks' / 'metadata' / f"{chunk_id}.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as mf:
                            metadata = json.load(mf)
                            found_chunks.append((chunk_id, metadata))
                    else:
                        found_chunks.append((chunk_id, {}))
        
        # Display results
        print(f"Found {len(found_chunks)} results:")
        for i, (chunk_id, metadata) in enumerate(found_chunks[:args.limit]):
            print(f"\nResult {i+1}:")
            print(f"- Chunk ID: {chunk_id}")
            
            # Display citation if available
            if "citation_text" in metadata:
                print(f"- Citation: {metadata['citation_text']}")
                
            # Display section info if available
            if "sections" in metadata and metadata["sections"]:
                section = metadata["sections"][0]
                print(f"- Section: {section.get('name', 'Unknown')}")
                if "start_line" in section and "end_line" in section:
                    print(f"- Lines: {section['start_line']}-{section['end_line']}")
                    
        return 0
    except Exception as e:
        logger.error(f"Error searching: {e}")
        print(f"Error: {e}")
        return 1

def main():
    args = parse_args()
    
    if args.version:
        print("Knowledge Management System v0.1.0")
        return 0
    
    if not args.command:
        print("No command specified. Use --help for usage information.")
        return 1
    
    # Load configuration
    config = load_config(args.config if hasattr(args, 'config') else None)
    
    # Handle commands
    if args.command == 'ingest':
        return handle_ingest(args, config)
    elif args.command == 'kb':
        if args.kb_command == 'create':
            return handle_kb_create(args, config)
        elif args.kb_command == 'list':
            return handle_kb_list(args, config)
        elif args.kb_command == 'status':
            return handle_kb_status(args, config)
        else:
            print(f"Unknown KB command: {args.kb_command}")
            return 1
    elif args.command == 'process':
        if args.process_command == 'create':
            return handle_process_create(args, config)
        else:
            print(f"Unknown process command: {args.process_command}")
            return 1
    elif args.command == 'map':
        if args.map_command == 'create':
            return handle_map_create(args, config)
        else:
            print(f"Unknown map command: {args.map_command}")
            return 1
    elif args.command == 'chunk':
        return handle_chunk(args, config)
    elif args.command == 'search':
        return handle_search(args, config)
    else:
        print(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())