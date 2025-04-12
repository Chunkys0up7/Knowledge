import os
import git
import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime

class KnowledgeBaseRepository:
    """Manages knowledge base repositories with proper structure and Git integration.
    
    Each knowledge base creates a dedicated Git repository with standardized structure:
    
    /kb_name/
    ├── raw/              # Original documents
    ├── processed/        # Processed markdown versions
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
    """
    
    def __init__(self, base_path="/data/knowledge_bases"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_kb(self, kb_name, description="", owner="", metadata=None):
        """Create a new knowledge base repository with standardized structure."""
        # Validate kb_name
        kb_name = self._sanitize_name(kb_name)
        
        # Create path for the new KB
        kb_path = self.base_path / kb_name
        
        if kb_path.exists():
            raise ValueError(f"Knowledge base '{kb_name}' already exists")
        
        # Create directories
        directories = [
            "raw",
            "processed",
            "metadata",
            "citations",
            "chunks/text",
            "chunks/metadata",
            "vectors",
            "workflows",
            "pdfs",
            "documentation/processes",
            "documentation/maps",
            "documentation/guides",
            "index"
        ]
        
        for directory in directories:
            (kb_path / directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize Git repository
        repo = git.Repo.init(kb_path)
        
        # Create README.md
        readme_content = f"# {kb_name} Knowledge Base\n\n"
        readme_content += f"{description}\n\n"
        readme_content += f"Created: {datetime.now().isoformat()}\n"
        readme_content += f"Owner: {owner}\n\n"
        readme_content += "## Structure\n\n"
        readme_content += "- `raw/`: Original documents\n"
        readme_content += "- `processed/`: Processed markdown versions\n"
        readme_content += "- `metadata/`: Document metadata\n"
        readme_content += "- `citations/`: Citation information\n"
        readme_content += "- `chunks/`: Chunked content for RAG\n"
        readme_content += "- `vectors/`: Vector embeddings\n"
        readme_content += "- `workflows/`: Processing workflow records\n"
        readme_content += "- `pdfs/`: PDF versions for citation\n"
        readme_content += "- `documentation/`: KB documentation\n"
        readme_content += "- `index/`: Index files\n"
        
        with open(kb_path / "README.md", 'w') as f:
            f.write(readme_content)
        
        # Create KB metadata
        kb_metadata = {
            "name": kb_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "owner": owner,
            "metadata": metadata or {},
            "uuid": str(uuid.uuid4())
        }
        
        with open(kb_path / "kb_info.json", 'w') as f:
            json.dump(kb_metadata, f, indent=2)
            
        # Create .gitignore
        gitignore_content = """
# Temporary files
*.tmp
*.temp
.DS_Store

# Vector files (optional, depending on size)
# vectors/*

# Large binary files
*.zip
*.gz
*.tar
        """
        
        with open(kb_path / ".gitignore", 'w') as f:
            f.write(gitignore_content)
            
        # Create initial commit
        repo.git.add(all=True)
        repo.index.commit(f"Initialize {kb_name} knowledge base")
        
        return kb_path
    
    def list_kbs(self):
        """List all knowledge bases."""
        kbs = []
        
        for item in self.base_path.iterdir():
            if item.is_dir() and (item / "kb_info.json").exists():
                try:
                    with open(item / "kb_info.json", 'r') as f:
                        kb_info = json.load(f)
                    kbs.append(kb_info)
                except:
                    # Skip if metadata file can't be read
                    pass
                    
        return kbs
    
    def get_kb(self, kb_name):
        """Get a knowledge base by name."""
        kb_path = self.base_path / kb_name
        
        if not kb_path.exists() or not (kb_path / "kb_info.json").exists():
            raise ValueError(f"Knowledge base '{kb_name}' not found")
            
        with open(kb_path / "kb_info.json", 'r') as f:
            kb_info = json.load(f)
            
        return {
            "info": kb_info,
            "path": kb_path,
            "repo": git.Repo(kb_path) if (kb_path / ".git").exists() else None
        }
    
    def add_document(self, kb_name, doc_id, processed_path, metadata, citation=None):
        """Add a document to a knowledge base."""
        kb = self.get_kb(kb_name)
        kb_path = kb["path"]
        
        # Copy processed document
        src_path = Path(processed_path)
        if not src_path.exists():
            raise ValueError(f"Source document doesn't exist: {processed_path}")
            
        # Determine destination based on document type
        content_type = metadata.get("content_type", "unknown")
        
        if content_type == "code":
            dest_dir = kb_path / "processed" / "code"
        elif content_type == "markdown":
            dest_dir = kb_path / "processed" / "markdown"
        elif content_type == "pdf":
            dest_dir = kb_path / "processed" / "documents"
        else:
            dest_dir = kb_path / "processed" / "other"
            
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{doc_id}.md"
        
        # Copy processed file
        shutil.copy2(src_path, dest_path)
        
        # Save metadata
        with open(kb_path / "metadata" / f"{doc_id}.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Save citation if provided
        if citation:
            with open(kb_path / "citations" / f"{doc_id}_citation.json", 'w') as f:
                json.dump(citation, f, indent=2)
                
        # Generate PDF for citation if not already a PDF
        if content_type != "pdf":
            self._generate_citation_pdf(kb_path, doc_id, dest_path)
                
        # If there's a Git repo, commit the changes
        if kb["repo"]:
            try:
                kb["repo"].git.add(str(dest_path))
                kb["repo"].git.add(str(kb_path / "metadata" / f"{doc_id}.json"))
                if citation:
                    kb["repo"].git.add(str(kb_path / "citations" / f"{doc_id}_citation.json"))
                    
                commit_msg = f"Add document: {metadata.get('title', doc_id)}"
                kb["repo"].index.commit(commit_msg)
            except Exception as e:
                print(f"Error committing to Git: {e}")
                
        return dest_path
    
    def add_chunks(self, kb_name, doc_id, chunks, chunk_metadata):
        """Add document chunks to a knowledge base."""
        kb = self.get_kb(kb_name)
        kb_path = kb["path"]
        
        # Ensure directories exist
        chunks_text_dir = kb_path / "chunks" / "text"
        chunks_metadata_dir = kb_path / "chunks" / "metadata"
        chunks_text_dir.mkdir(parents=True, exist_ok=True)
        chunks_metadata_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_files = []
        
        # Save each chunk and its metadata
        for i, (chunk, metadata) in enumerate(zip(chunks, chunk_metadata)):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Save chunk text
            chunk_file = chunks_text_dir / f"{chunk_id}.txt"
            with open(chunk_file, 'w') as f:
                f.write(chunk)
                
            # Save chunk metadata
            metadata_file = chunks_metadata_dir / f"{chunk_id}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            chunk_files.append({
                "chunk_id": chunk_id,
                "text_path": str(chunk_file.relative_to(kb_path)),
                "metadata_path": str(metadata_file.relative_to(kb_path))
            })
                
        # Update document metadata to reference chunks
        metadata_path = kb_path / "metadata" / f"{doc_id}.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                doc_metadata = json.load(f)
                
            doc_metadata["chunks"] = chunk_files
            
            with open(metadata_path, 'w') as f:
                json.dump(doc_metadata, f, indent=2)
                
        # If there's a Git repo, commit the changes
        if kb["repo"]:
            try:
                kb["repo"].git.add(str(chunks_text_dir))
                kb["repo"].git.add(str(chunks_metadata_dir))
                kb["repo"].git.add(str(metadata_path))
                
                commit_msg = f"Add chunks for document: {doc_id}"
                kb["repo"].index.commit(commit_msg)
            except Exception as e:
                print(f"Error committing to Git: {e}")
                
        return chunk_files
    
    def update_documentation(self, kb_name, doc_type, name, content, commit_msg=None):
        """Update documentation for a knowledge base."""
        kb = self.get_kb(kb_name)
        kb_path = kb["path"]
        
        # Validate doc_type
        if doc_type not in ["process", "map", "guide"]:
            raise ValueError(f"Invalid documentation type: {doc_type}")
            
        # Determine documentation directory
        if doc_type == "process":
            doc_dir = kb_path / "documentation" / "processes"
        elif doc_type == "map":
            doc_dir = kb_path / "documentation" / "maps"
        else:  # guide
            doc_dir = kb_path / "documentation" / "guides"
            
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize name and create file path
        file_name = self._sanitize_name(name)
        file_path = doc_dir / f"{file_name}.md"
        
        # Write content
        with open(file_path, 'w') as f:
            f.write(content)
            
        # If there's a Git repo, commit the changes
        if kb["repo"]:
            try:
                kb["repo"].git.add(str(file_path))
                
                if not commit_msg:
                    commit_msg = f"Update {doc_type} documentation: {name}"
                    
                kb["repo"].index.commit(commit_msg)
            except Exception as e:
                print(f"Error committing to Git: {e}")
                
        return file_path
    
    def clone_kb(self, kb_name, destination):
        """Clone a knowledge base to a new location."""
        kb = self.get_kb(kb_name)
        kb_path = kb["path"]
        
        destination_path = Path(destination) / kb_name
        
        if destination_path.exists():
            raise ValueError(f"Destination already exists: {destination_path}")
            
        # If there's a Git repo, use Git clone
        if kb["repo"]:
            git.Repo.clone_from(kb_path, destination_path)
        else:
            # Otherwise, copy the directory
            shutil.copytree(kb_path, destination_path)
            
        return destination_path
    
    def _sanitize_name(self, name):
        """Sanitize a name for use in paths."""
        # Replace spaces with underscores and remove special characters
        return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).replace(" ", "_").lower()
    
    def _generate_citation_pdf(self, kb_path, doc_id, source_path):
        """Generate a PDF version of the document for citation purposes.
        
        This is a placeholder - in a real implementation, 
        this would convert the document to a PDF.
        """
        # Create placeholder file
        pdf_dir = kb_path / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = pdf_dir / f"{doc_id}.txt"
        with open(pdf_path, 'w') as f:
            f.write(f"PDF citation version of document {doc_id}\n")
            f.write(f"Source: {source_path}\n")
            
        return pdf_path