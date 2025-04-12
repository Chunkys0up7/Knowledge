#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
import logging
import threading
import queue
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify, send_from_directory

# Add parent directory to path to import modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from ingestor.bulk_ingestor import BulkIngestor, SimpleImageProcessor
from processor.chunker import SemanticChunker
from processor.kb_repository import KnowledgeBaseRepository
from processor.citation_processor import CitationProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ui.log')
    ]
)
logger = logging.getLogger('knowledge_ui')

app = Flask(__name__, static_folder='static')

# Configuration
app.config['UPLOAD_FOLDER'] = '/tmp/kb_uploads'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max payload
app.config['KB_BASE_DIR'] = '/data/knowledge_bases'
app.config['RESOURCE_LIMITS'] = {
    'max_workers': 4,  # Maximum concurrent worker threads
    'chunk_size': 10,  # Process files in chunks of 10
    'memory_limit': 1024 * 1024 * 1024,  # 1GB memory limit (soft limit)
}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Processing queue - global to keep track of long-running tasks
processing_queue = queue.Queue()
active_tasks = {}
completed_tasks = {}

# Initialize KB repository
kb_repo = KnowledgeBaseRepository(base_path=app.config['KB_BASE_DIR'])

# Worker thread manager
worker_lock = threading.Lock()
worker_count = 0
worker_event = threading.Event()

def worker_thread():
    """Worker thread to process documents from the queue."""
    global worker_count
    
    while True:
        try:
            # Wait for a task
            task = processing_queue.get(timeout=5)
            
            # Process the task
            try:
                if task['type'] == 'process_batch':
                    process_batch(task)
                elif task['type'] == 'create_maps':
                    create_maps(task)
                elif task['type'] == 'chunk_documents':
                    chunk_documents(task)
            except Exception as e:
                logger.error(f"Error processing task {task['id']}: {e}")
                task['status'] = 'error'
                task['error'] = str(e)
                
            # Mark task as done
            processing_queue.task_done()
            
        except queue.Empty:
            # Check if we should terminate
            if worker_event.is_set():
                break
                
    # Decrement worker count
    with worker_lock:
        worker_count -= 1

def ensure_workers():
    """Ensure enough worker threads are running."""
    global worker_count
    
    with worker_lock:
        needed = max(0, min(processing_queue.qsize(), 
                          app.config['RESOURCE_LIMITS']['max_workers'] - worker_count))
        
        # Start new workers if needed
        for _ in range(needed):
            thread = threading.Thread(target=worker_thread)
            thread.daemon = True
            thread.start()
            worker_count += 1
            logger.info(f"Started worker thread, total: {worker_count}")

def process_batch(task):
    """Process a batch of documents."""
    try:
        # Update task status
        task['status'] = 'processing'
        task['progress'] = 0
        active_tasks[task['id']] = task
        
        # Setup progress tracking
        total_files = len(task['files'])
        processed_files = 0
        
        # Create the bulk ingestor
        ingestor = BulkIngestor(
            output_dir=task['output_dir'],
            kb_name=task['kb_name'],
            image_processor=SimpleImageProcessor()
        )
        
        # Process files in chunks to control memory usage
        chunk_size = app.config['RESOURCE_LIMITS']['chunk_size']
        success_files = []
        
        for i in range(0, len(task['files']), chunk_size):
            chunk = task['files'][i:i+chunk_size]
            
            # Process each file in the chunk
            for file_path in chunk:
                try:
                    doc_id = ingestor.process_file(file_path)
                    if doc_id:
                        success_files.append(doc_id)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    
                # Update progress
                processed_files += 1
                task['progress'] = (processed_files / total_files) * 100
                
            # Brief pause to allow system to recover resources
            time.sleep(0.1)
            
        # Create index file
        index_file = Path(task['output_dir']) / "index" / "document_index.json"
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        
        with open(index_file, 'w') as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "document_count": len(success_files),
                "documents": success_files,
                "batch_id": task['id']
            }, f, indent=2)
            
        # Update task result
        task['status'] = 'completed'
        task['progress'] = 100
        task['result'] = {
            'total_files': total_files,
            'processed_files': len(success_files),
            'doc_ids': success_files
        }
        task['completed_at'] = datetime.now().isoformat()
        
        # Move from active to completed
        completed_tasks[task['id']] = task
        active_tasks.pop(task['id'], None)
        
    except Exception as e:
        logger.error(f"Error in process_batch: {e}")
        task['status'] = 'error'
        task['error'] = str(e)
        active_tasks[task['id']] = task

def create_maps(task):
    """Create knowledge maps for a batch of documents."""
    try:
        # Update task status
        task['status'] = 'processing'
        task['progress'] = 0
        active_tasks[task['id']] = task
        
        # Create the bulk ingestor
        ingestor = BulkIngestor(
            output_dir=task['output_dir'],
            kb_name=task['kb_name'],
            image_processor=SimpleImageProcessor()
        )
        
        # Get document metadata
        kb = kb_repo.get_kb(task['kb_name'])
        metadata_dir = kb['path'] / 'metadata'
        
        # Group documents by type
        code_docs = []
        markdown_docs = []
        document_docs = []
        other_docs = []
        
        for doc_id in task['doc_ids']:
            metadata_file = metadata_dir / f"{doc_id}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    content_type = metadata.get('content_type', 'unknown')
                    
                    if content_type == 'code':
                        code_docs.append(doc_id)
                    elif content_type == 'markdown':
                        markdown_docs.append(doc_id)
                    elif content_type in ['document', 'pdf']:
                        document_docs.append(doc_id)
                    else:
                        other_docs.append(doc_id)
        
        # Create maps
        maps = []
        
        # Create overall map
        if task['doc_ids']:
            map_name = ingestor.generate_knowledge_map(
                f"All Documents ({len(task['doc_ids'])})",
                task['doc_ids']
            )
            maps.append(map_name)
            
        # Create type-specific maps
        if code_docs:
            map_name = ingestor.generate_knowledge_map(
                f"Code Files ({len(code_docs)})",
                code_docs
            )
            maps.append(map_name)
            
        if markdown_docs:
            map_name = ingestor.generate_knowledge_map(
                f"Documentation ({len(markdown_docs)})",
                markdown_docs
            )
            maps.append(map_name)
            
        if document_docs:
            map_name = ingestor.generate_knowledge_map(
                f"Documents ({len(document_docs)})",
                document_docs
            )
            maps.append(map_name)
        
        # Create process documentation
        process_content = f"""# Batch Processing {task['id']}

This batch contains {len(task['doc_ids'])} documents processed on {datetime.now().isoformat()}.

## Document Types
- Code files: {len(code_docs)}
- Documentation: {len(markdown_docs)}
- Documents/PDFs: {len(document_docs)}
- Other files: {len(other_docs)}

## Processing Details
- Batch ID: {task['id']}
- Knowledge Base: {task['kb_name']}
- Started: {task.get('created_at', 'Unknown')}
- Completed: {datetime.now().isoformat()}
"""
        
        process_name = ingestor.generate_process_documentation(
            f"Batch Processing {task['id'][:8]}",
            process_content
        )
        
        # Update task result
        task['status'] = 'completed'
        task['progress'] = 100
        task['result'] = {
            'maps': maps,
            'process_documentation': process_name
        }
        task['completed_at'] = datetime.now().isoformat()
        
        # Move from active to completed
        completed_tasks[task['id']] = task
        active_tasks.pop(task['id'], None)
        
    except Exception as e:
        logger.error(f"Error in create_maps: {e}")
        task['status'] = 'error'
        task['error'] = str(e)
        active_tasks[task['id']] = task]

def chunk_documents(task):
    """Chunk documents for RAG."""
    try:
        # Update task status
        task['status'] = 'processing'
        task['progress'] = 0
        active_tasks[task['id']] = task
        
        # Create the bulk ingestor and chunker
        ingestor = BulkIngestor(
            output_dir=task['output_dir'],
            kb_name=task['kb_name'],
            image_processor=SimpleImageProcessor()
        )
        
        chunker = SemanticChunker(
            max_tokens=task.get('max_tokens', 512),
            overlap=task.get('overlap', 64)
        )
        
        # Setup progress tracking
        total_docs = len(task['doc_ids'])
        processed_docs = 0
        total_chunks = 0
        
        # Process documents in chunks to control memory usage
        chunk_size = min(app.config['RESOURCE_LIMITS']['chunk_size'], 5)  # Smaller chunks for chunking
        
        for i in range(0, len(task['doc_ids']), chunk_size):
            doc_chunk = task['doc_ids'][i:i+chunk_size]
            
            # Process each document in the chunk
            for doc_id in doc_chunk:
                try:
                    chunk_count = ingestor.chunk_document(doc_id, chunker)
                    total_chunks += chunk_count
                except Exception as e:
                    logger.error(f"Error chunking document {doc_id}: {e}")
                    
                # Update progress
                processed_docs += 1
                task['progress'] = (processed_docs / total_docs) * 100
                
            # Brief pause to allow system to recover resources
            time.sleep(0.5)  # Longer pause as chunking is memory-intensive
            
        # Update task result
        task['status'] = 'completed'
        task['progress'] = 100
        task['result'] = {
            'total_documents': total_docs,
            'total_chunks': total_chunks
        }
        task['completed_at'] = datetime.now().isoformat()
        
        # Move from active to completed
        completed_tasks[task['id']] = task
        active_tasks.pop(task['id'], None)
        
    except Exception as e:
        logger.error(f"Error in chunk_documents: {e}")
        task['status'] = 'error'
        task['error'] = str(e)
        active_tasks[task['id']] = task]

# Routes
@app.route('/')
def index():
    """Render the main page."""
    # Get list of knowledge bases
    kbs = kb_repo.list_kbs()
    
    return render_template('index.html', kbs=kbs)

@app.route('/api/kbs', methods=['GET'])
def get_kbs():
    """Get list of knowledge bases."""
    kbs = kb_repo.list_kbs()
    return jsonify(kbs)

@app.route('/api/kbs', methods=['POST'])
def create_kb():
    """Create a new knowledge base."""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        owner = data.get('owner', 'UI User')
        
        if not name:
            return jsonify({'error': 'Missing name parameter'}), 400
            
        # Create KB
        kb_path = kb_repo.create_kb(name, description, owner)
        
        return jsonify({
            'status': 'success',
            'message': f'Knowledge base {name} created successfully',
            'path': str(kb_path)
        })
        
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/kbs/<kb_name>/status', methods=['GET'])
def get_kb_status(kb_name):
    """Get knowledge base status."""
    try:
        kb = kb_repo.get_kb(kb_name)
        kb_path = kb['path']
        kb_info = kb['info']
        
        # Count files in directories
        def count_files(dir_path):
            if not dir_path.exists():
                return 0
            return sum(1 for _ in dir_path.glob("**/*") if _.is_file())
        
        status = {
            'name': kb_info['name'],
            'description': kb_info.get('description', 'No description'),
            'created_at': kb_info.get('created_at', 'Unknown'),
            'owner': kb_info.get('owner', 'Unknown'),
            'path': str(kb_path),
            'stats': {
                'raw_files': count_files(kb_path / 'raw'),
                'processed_files': count_files(kb_path / 'processed'),
                'metadata_files': count_files(kb_path / 'metadata'),
                'citation_files': count_files(kb_path / 'citations'),
                'chunks': count_files(kb_path / 'chunks'),
                'documentation': count_files(kb_path / 'documentation')
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting knowledge base status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads."""
    try:
        # Get form data
        kb_name = request.form.get('kb_name')
        if not kb_name:
            return jsonify({'error': 'Missing kb_name parameter'}), 400
            
        # Check if KB exists
        try:
            kb = kb_repo.get_kb(kb_name)
        except:
            return jsonify({'error': f'Knowledge base {kb_name} not found'}), 404
            
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
            
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
            
        # Create a unique batch ID
        batch_id = str(uuid.uuid4())
        batch_dir = Path(app.config['UPLOAD_FOLDER']) / batch_id
        os.makedirs(batch_dir, exist_ok=True)
        
        # Save uploaded files
        saved_files = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = batch_dir / filename
            file.save(file_path)
            saved_files.append(str(file_path))
            
        # Create processing task
        task_id = str(uuid.uuid4())
        output_dir = str(kb['path'])
        
        task = {
            'id': task_id,
            'type': 'process_batch',
            'status': 'queued',
            'kb_name': kb_name,
            'files': saved_files,
            'output_dir': output_dir,
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        # Add to processing queue
        processing_queue.put(task)
        active_tasks[task_id] = task
        
        # Ensure workers are running
        ensure_workers()
        
        return jsonify({
            'status': 'success',
            'message': f'Upload successful, processing {len(saved_files)} files',
            'task_id': task_id,
            'batch_id': batch_id
        })
        
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get task status."""
    if task_id in active_tasks:
        return jsonify(active_tasks[task_id])
    elif task_id in completed_tasks:
        return jsonify(completed_tasks[task_id])
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """Get all tasks."""
    all_tasks = {
        'active': list(active_tasks.values()),
        'completed': list(completed_tasks.values())
    }
    return jsonify(all_tasks)

@app.route('/api/create_maps', methods=['POST'])
def api_create_maps():
    """Create knowledge maps for documents."""
    try:
        data = request.json
        kb_name = data.get('kb_name')
        doc_ids = data.get('doc_ids', [])
        
        if not kb_name:
            return jsonify({'error': 'Missing kb_name parameter'}), 400
            
        # Check if KB exists
        try:
            kb = kb_repo.get_kb(kb_name)
        except:
            return jsonify({'error': f'Knowledge base {kb_name} not found'}), 404
            
        if not doc_ids:
            return jsonify({'error': 'No documents specified'}), 400
            
        # Create task
        task_id = str(uuid.uuid4())
        output_dir = str(kb['path'])
        
        task = {
            'id': task_id,
            'type': 'create_maps',
            'status': 'queued',
            'kb_name': kb_name,
            'doc_ids': doc_ids,
            'output_dir': output_dir,
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        # Add to processing queue
        processing_queue.put(task)
        active_tasks[task_id] = task
        
        # Ensure workers are running
        ensure_workers()
        
        return jsonify({
            'status': 'success',
            'message': f'Creating maps for {len(doc_ids)} documents',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f"Error creating maps: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chunk_documents', methods=['POST'])
def api_chunk_documents():
    """Chunk documents for RAG."""
    try:
        data = request.json
        kb_name = data.get('kb_name')
        doc_ids = data.get('doc_ids', [])
        max_tokens = data.get('max_tokens', 512)
        overlap = data.get('overlap', 64)
        
        if not kb_name:
            return jsonify({'error': 'Missing kb_name parameter'}), 400
            
        # Check if KB exists
        try:
            kb = kb_repo.get_kb(kb_name)
        except:
            return jsonify({'error': f'Knowledge base {kb_name} not found'}), 404
            
        if not doc_ids:
            return jsonify({'error': 'No documents specified'}), 400
            
        # Create task
        task_id = str(uuid.uuid4())
        output_dir = str(kb['path'])
        
        task = {
            'id': task_id,
            'type': 'chunk_documents',
            'status': 'queued',
            'kb_name': kb_name,
            'doc_ids': doc_ids,
            'output_dir': output_dir,
            'max_tokens': max_tokens,
            'overlap': overlap,
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        # Add to processing queue
        processing_queue.put(task)
        active_tasks[task_id] = task
        
        # Ensure workers are running
        ensure_workers()
        
        return jsonify({
            'status': 'success',
            'message': f'Chunking {len(doc_ids)} documents',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f"Error chunking documents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_workflow', methods=['POST'])
def api_process_workflow():
    """Execute a complete workflow - process, map, and chunk documents."""
    try:
        # Get form data
        kb_name = request.form.get('kb_name')
        if not kb_name:
            return jsonify({'error': 'Missing kb_name parameter'}), 400
            
        # Check if KB exists
        try:
            kb = kb_repo.get_kb(kb_name)
        except:
            return jsonify({'error': f'Knowledge base {kb_name} not found'}), 404
            
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
            
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
            
        # Create a unique batch ID
        batch_id = str(uuid.uuid4())
        batch_dir = Path(app.config['UPLOAD_FOLDER']) / batch_id
        os.makedirs(batch_dir, exist_ok=True)
        
        # Save uploaded files
        saved_files = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = batch_dir / filename
            file.save(file_path)
            saved_files.append(str(file_path))
            
        # Create workflow task - we'll track this task ID
        workflow_id = str(uuid.uuid4())
        output_dir = str(kb['path'])
        
        # 1. Create ingestion task
        ingest_task_id = str(uuid.uuid4())
        ingest_task = {
            'id': ingest_task_id,
            'type': 'process_batch',
            'status': 'queued',
            'kb_name': kb_name,
            'files': saved_files,
            'output_dir': output_dir,
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'workflow_id': workflow_id,
            'workflow_step': 1
        }
        
        # Add a workflow tracking task
        workflow_task = {
            'id': workflow_id,
            'type': 'workflow',
            'status': 'in_progress',
            'kb_name': kb_name,
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'tasks': [ingest_task_id],
            'current_step': 1,
            'total_steps': 3,
            'result': {}
        }
        
        # Add tasks to queue
        processing_queue.put(ingest_task)
        active_tasks[ingest_task_id] = ingest_task
        active_tasks[workflow_id] = workflow_task
        
        # Ensure workers are running
        ensure_workers()
        
        return jsonify({
            'status': 'success',
            'message': f'Started workflow for {len(saved_files)} files',
            'workflow_id': workflow_id,
            'batch_id': batch_id
        })
        
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        return jsonify({'error': str(e)}), 500

# Serve static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Main entry point
if __name__ == '__main__':
    # Start worker threads
    for _ in range(2):  # Start with 2 workers
        thread = threading.Thread(target=worker_thread)
        thread.daemon = True
        thread.start()
        worker_count += 1
        
    # Start the app
    app.run(host='0.0.0.0', port=5000, debug=True)