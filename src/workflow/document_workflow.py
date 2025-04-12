#!/usr/bin/env python3
import os
import yaml
import json
import argparse
import logging
import shutil
from pathlib import Path
import git
import time
import hashlib
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('workflow.log')
    ]
)
logger = logging.getLogger('document_workflow')

class DocumentWorkflow:
    """Automated workflow for document processing in the knowledge base.
    
    Features:
    - Watch directories for new documents
    - Process documents in batches
    - Generate workflow metadata
    - Track document lineage and versioning
    - Integrate with Git for version control
    """
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.watch_dirs = self.config.get('watch_directories', [])
        self.output_dir = Path(self.config.get('output_dir', '/data/knowledge_base'))
        self.workflow_dir = self.output_dir / "workflows"
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Git repository
        if not (self.output_dir / ".git").exists():
            self.repo = git.Repo.init(self.output_dir)
        else:
            self.repo = git.Repo(self.output_dir)
            
        # Create workflow tracking file if it doesn't exist
        self.workflow_file = self.workflow_dir / "workflow_tracking.json"
        if not self.workflow_file.exists():
            with open(self.workflow_file, 'w') as f:
                json.dump({
                    "workflows": [],
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
    
    def _load_config(self, config_path=None):
        """Load configuration from YAML file."""
        default_config = {
            'output_dir': '/data/knowledge_base',
            'watch_directories': [],
            'polling_interval': 300,  # 5 minutes
            'batch_size': 100,
            'git_auto_commit': True,
            'git_commit_interval': 1800,  # 30 minutes
            'workflow': {
                'track_lineage': True,
                'generate_stats': True
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge configs
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return default_config
    
    def watch_directories(self):
        """Watch directories for new files and process them."""
        logger.info(f"Starting directory watch on {self.watch_dirs}")
        
        if not self.watch_dirs:
            logger.error("No watch directories configured")
            return
            
        try:
            while True:
                self.process_new_documents()
                
                # Sleep for the configured interval
                time.sleep(self.config.get('polling_interval', 300))
        except KeyboardInterrupt:
            logger.info("Directory watch stopped by user")
    
    def process_new_documents(self):
        """Process any new documents in the watch directories."""
        # Get list of files in watch directories
        all_files = []
        for watch_dir in self.watch_dirs:
            watch_path = Path(watch_dir)
            if not watch_path.exists():
                logger.warning(f"Watch directory doesn't exist: {watch_dir}")
                continue
                
            for root, _, files in os.walk(watch_path):
                for file in files:
                    file_path = Path(root) / file
                    all_files.append(file_path)
        
        # Get list of already processed files
        processed_files = self._get_processed_files()
        
        # Find new files
        new_files = []
        for file_path in all_files:
            file_hash = self._hash_file(file_path)
            if file_hash not in processed_files:
                new_files.append(file_path)
        
        if not new_files:
            logger.info("No new files to process")
            return
            
        logger.info(f"Found {len(new_files)} new files to process")
        
        # Process files in batches
        batch_size = self.config.get('batch_size', 100)
        for i in range(0, len(new_files), batch_size):
            batch = new_files[i:i+batch_size]
            self._process_batch(batch, i//batch_size)
    
    def _process_batch(self, files, batch_num):
        """Process a batch of files and create a workflow record."""
        logger.info(f"Processing batch {batch_num} with {len(files)} files")
        
        # Create a workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{batch_num}"
        
        # Create workflow directory
        workflow_dir = self.workflow_dir / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest file
        manifest = {
            "workflow_id": workflow_id,
            "created_at": datetime.now().isoformat(),
            "file_count": len(files),
            "files": [],
            "status": "in_progress"
        }
        
        # Copy files to workflow directory
        for file_path in files:
            try:
                # Create a hash-based filename to avoid collisions
                file_hash = self._hash_file(file_path)
                dest_path = workflow_dir / f"{file_hash}{file_path.suffix}"
                
                # Copy the file
                shutil.copy2(file_path, dest_path)
                
                # Add to manifest
                manifest["files"].append({
                    "original_path": str(file_path),
                    "workflow_path": str(dest_path.relative_to(self.output_dir)),
                    "file_hash": file_hash,
                    "file_size": file_path.stat().st_size,
                    "file_type": file_path.suffix.lower()[1:] if file_path.suffix else "unknown"
                })
                
                logger.debug(f"Copied {file_path} to {dest_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        # Update manifest status
        manifest["status"] = "copied"
        
        # Save manifest
        manifest_path = workflow_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Update workflow tracking
        self._update_workflow_tracking(workflow_id, manifest)
        
        # Create processing script
        self._create_processing_script(workflow_dir, workflow_id)
        
        # Commit to Git if configured
        if self.config.get('git_auto_commit', True):
            self._commit_workflow(workflow_id, len(files))
            
        logger.info(f"Batch {batch_num} processing completed, workflow_id: {workflow_id}")
        
        return workflow_id
    
    def _create_processing_script(self, workflow_dir, workflow_id):
        """Create a processing script for the workflow."""
        script_path = workflow_dir / "process.py"
        
        script_content = f"""#!/usr/bin/env python3
# Auto-generated processing script for workflow {workflow_id}
# Created at: {datetime.now().isoformat()}

import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import modules
parent_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from ingestor.bulk_ingestor import BulkIngestor, SimpleImageProcessor
from ingestor.smart_ingestor import SmartIngestor
from storage.document_store import DocumentStore

def main():
    # Load manifest
    manifest_path = Path(__file__).parent / "manifest.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    print(f"Processing workflow {{manifest['workflow_id']}} with {{manifest['file_count']}} files")
    
    # Initialize components
    ingestor = BulkIngestor(
        output_dir="{self.output_dir}",
        image_processor=SimpleImageProcessor(),
        smart_ingestor=SmartIngestor(),
        document_store=DocumentStore()
    )
    
    # Process each file
    processed_files = []
    for file_info in manifest['files']:
        workflow_path = Path("{self.output_dir}") / file_info['workflow_path']
        if workflow_path.exists():
            print(f"Processing {{workflow_path}}")
            try:
                doc_id = ingestor.process_file(workflow_path)
                if doc_id:
                    processed_files.append(doc_id)
            except Exception as e:
                print(f"Error processing {{workflow_path}}: {{e}}")
    
    # Update manifest
    manifest['status'] = 'processed'
    manifest['processed_files'] = processed_files
    manifest['processed_at'] = "{datetime.now().isoformat()}"
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Processing completed: {{len(processed_files)}} files processed successfully")

if __name__ == "__main__":
    main()
"""
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
    
    def _update_workflow_tracking(self, workflow_id, manifest):
        """Update the workflow tracking file."""
        if self.workflow_file.exists():
            with open(self.workflow_file, 'r') as f:
                tracking = json.load(f)
        else:
            tracking = {"workflows": [], "last_updated": datetime.now().isoformat()}
        
        # Add new workflow
        tracking["workflows"].append({
            "workflow_id": workflow_id,
            "created_at": manifest["created_at"],
            "file_count": manifest["file_count"],
            "status": manifest["status"]
        })
        
        tracking["last_updated"] = datetime.now().isoformat()
        
        # Save tracking file
        with open(self.workflow_file, 'w') as f:
            json.dump(tracking, f, indent=2)
    
    def _get_processed_files(self):
        """Get a set of already processed file hashes."""
        processed_files = set()
        
        # Check all workflow manifests
        for manifest_file in self.workflow_dir.glob("*/manifest.json"):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    for file_info in manifest.get("files", []):
                        if "file_hash" in file_info:
                            processed_files.add(file_info["file_hash"])
            except Exception as e:
                logger.error(f"Error reading manifest {manifest_file}: {e}")
        
        return processed_files
    
    def _hash_file(self, file_path):
        """Generate a hash for a file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    
    def _commit_workflow(self, workflow_id, file_count):
        """Commit workflow changes to Git."""
        try:
            # Add workflow files
            workflow_path = self.workflow_dir / workflow_id
            self.repo.git.add(str(workflow_path))
            
            # Add tracking file
            self.repo.git.add(str(self.workflow_file))
            
            # Commit
            commit_msg = f"Added workflow {workflow_id} with {file_count} files"
            self.repo.index.commit(commit_msg)
            
            logger.info(f"Committed workflow {workflow_id} to Git")
        except Exception as e:
            logger.error(f"Error committing to Git: {e}")
    
    def run_workflow(self, workflow_id):
        """Run a specific workflow processing script."""
        workflow_dir = self.workflow_dir / workflow_id
        script_path = workflow_dir / "process.py"
        
        if not script_path.exists():
            logger.error(f"Workflow script not found: {script_path}")
            return False
        
        try:
            logger.info(f"Running workflow script for {workflow_id}")
            os.system(f"python {script_path}")
            
            # If configured, commit processed results
            if self.config.get('git_auto_commit', True):
                self.repo.git.add(self.output_dir / "raw")
                self.repo.git.add(self.output_dir / "processed")
                self.repo.git.add(self.output_dir / "metadata")
                self.repo.git.add(self.output_dir / "text")
                self.repo.git.add(self.output_dir / "index")
                self.repo.git.add(workflow_dir)
                
                commit_msg = f"Processed workflow {workflow_id}"
                self.repo.index.commit(commit_msg)
                
            return True
        except Exception as e:
            logger.error(f"Error running workflow {workflow_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Document Processing Workflow')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--watch', action='store_true', help='Watch directories for new files')
    parser.add_argument('--run-workflow', help='Run a specific workflow')
    
    args = parser.parse_args()
    
    workflow = DocumentWorkflow(args.config)
    
    if args.watch:
        workflow.watch_directories()
    elif args.run_workflow:
        workflow.run_workflow(args.run_workflow)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()