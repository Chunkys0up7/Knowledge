import os
import shutil
import hashlib
import json
from pathlib import Path
import git
from datetime import datetime
import re
import base64

from processor.citation_processor import CitationProcessor
from processor.kb_repository import KnowledgeBaseRepository

class BulkIngestor:
    """Process directories of documents for the knowledge base.
    
    Features:
    - Recursively processes directories
    - Creates metadata for each document
    - Handles code and markdown files
    - Extracts and transforms images to text descriptions
    - Creates an indexed data structure
    - Commits all processed content to git
    - Adds citation information to all documents
    - Organizes documents in the repository structure
    """
    
    def __init__(self, 
                 output_dir="/data/knowledge_base",
                 kb_name=None,
                 smart_ingestor=None,
                 document_store=None,
                 image_processor=None):
        """Initialize a bulk ingestor."""
        self.output_dir = Path(output_dir)
        self.smart_ingestor = smart_ingestor
        self.document_store = document_store
        self.image_processor = image_processor
        self.kb_name = kb_name or "default_kb"
        self.citation_processor = CitationProcessor(output_dir)
        self.kb_repo = KnowledgeBaseRepository()
        
        # Ensure knowledge base exists
        try:
            self.kb_repo.get_kb(self.kb_name)
        except ValueError:
            # Create new knowledge base if it doesn't exist
            self.kb_repo.create_kb(
                self.kb_name, 
                description=f"Knowledge base created on {datetime.now().isoformat()}",
                owner="bulk_ingestor"
            )
        
        # Create output directories if they don't exist
        self.raw_dir = self.output_dir / "raw"
        self.processed_dir = self.output_dir / "processed"
        self.metadata_dir = self.output_dir / "metadata"
        self.text_dir = self.output_dir / "text"
        self.index_dir = self.output_dir / "index"
        
        for dir_path in [self.raw_dir, self.processed_dir, self.metadata_dir, 
                         self.text_dir, self.index_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize git repo if it doesn't exist
        if not (self.output_dir / ".git").exists():
            self.repo = git.Repo.init(self.output_dir)
        else:
            self.repo = git.Repo(self.output_dir)
            
    def process_directory(self, input_dir):
        """Process all files in a directory recursively."""
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
            
        # Get list of all files
        all_files = []
        for root, _, files in os.walk(input_path):
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)
                
        # Process each file
        processed_files = []
        for file_path in all_files:
            try:
                doc_id = self.process_file(file_path)
                if doc_id:
                    processed_files.append(doc_id)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                
        # Create index file
        index_file = self.index_dir / "document_index.json"
        with open(index_file, 'w') as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "document_count": len(processed_files),
                "documents": processed_files
            }, f, indent=2)
            
        # Commit all changes
        self._commit_changes(f"Processed {len(processed_files)} documents from {input_path.name}")
        
        return processed_files
    
    def process_file(self, file_path):
        """Process a single file and return its document ID."""
        file_path = Path(file_path)
        
        # Skip hidden files and directories
        if file_path.name.startswith('.'):
            return None
            
        # Generate a unique document ID
        doc_id = self._generate_doc_id(file_path)
        
        # Copy the original file to raw directory
        raw_file = self.raw_dir / doc_id / file_path.name
        raw_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, raw_file)
        
        # Generate metadata
        metadata = self._create_metadata(file_path, doc_id)
        metadata_file = self.metadata_dir / f"{doc_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Process file based on type
        if self._is_image_file(file_path):
            if self.image_processor:
                # Extract text from image
                image_text = self.image_processor.extract_text(file_path)
                processed_content = f"Image Description: {image_text}"
            else:
                processed_content = f"[Image: {file_path.name}]"
        elif self._is_code_file(file_path):
            processed_content = self._process_code_file(file_path)
        elif self._is_markdown_file(file_path):
            processed_content = self._process_markdown_file(file_path)
        else:
            # Use SmartIngestor for other file types if available
            if self.smart_ingestor:
                processed_content = self.smart_ingestor.process(str(file_path))
            else:
                # Basic fallback - just read text files
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        processed_content = f.read()
                except UnicodeDecodeError:
                    processed_content = f"[Binary file: {file_path.name}]"
        
        # Save processed content
        processed_file = self.processed_dir / f"{doc_id}.md"
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
            
        # Create plain text version for RAG
        text_file = self.text_dir / f"{doc_id}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(self._convert_to_plain_text(processed_content))
            
        # Process for citations
        citation = self.citation_processor.process_document(
            file_path, doc_id, metadata
        )
        
        # Add to KB repository
        self.kb_repo.add_document(
            self.kb_name, 
            doc_id, 
            processed_file, 
            metadata, 
            citation
        )
            
        # Store in document store if available
        if self.document_store:
            self.document_store.store_document(processed_content, metadata)
            
        return doc_id
    
    def chunk_document(self, doc_id, chunker):
        """Chunk a document for RAG and add chunks to the KB repo."""
        # Get document text
        text_file = self.text_dir / f"{doc_id}.txt"
        if not text_file.exists():
            raise ValueError(f"Document text not found: {doc_id}")
            
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Chunk the document
        chunks = chunker.chunk(text)
        
        # Generate citation info for chunks
        chunk_citations = self.citation_processor.generate_chunk_citations(chunks, doc_id)
        
        # Add chunks to KB repository
        self.kb_repo.add_chunks(self.kb_name, doc_id, chunks, chunk_citations)
        
        return len(chunks)
    
    def generate_process_documentation(self, process_name, content, template=None):
        """Create process documentation in the knowledge base."""
        if template:
            # Merge template with content
            process_content = template.replace("{{content}}", content)
        else:
            process_content = f"# {process_name}\n\n{content}\n\n"
            process_content += f"Generated: {datetime.now().isoformat()}\n"
            
        # Add to KB repository
        self.kb_repo.update_documentation(
            self.kb_name,
            "process",
            process_name,
            process_content
        )
        
        return process_name
    
    def generate_knowledge_map(self, map_name, documents, relationships=None):
        """Generate a knowledge map for the documents in the KB."""
        # Create mermaid diagram
        mermaid = "```mermaid\ngraph TD\n"
        
        # Add document nodes
        for doc_id in documents:
            # Get document metadata
            metadata_file = self.metadata_dir / f"{doc_id}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                title = metadata.get("title", doc_id)
                mermaid += f"    {doc_id}[{title}]\n"
        
        # Add relationships
        if relationships:
            for rel in relationships:
                mermaid += f"    {rel['source']} -- {rel['label']} --> {rel['target']}\n"
        
        mermaid += "```\n\n"
        
        # Add description
        content = f"# Knowledge Map: {map_name}\n\n"
        content += "This map shows the relationships between documents in the knowledge base.\n\n"
        content += mermaid
        content += f"\nGenerated: {datetime.now().isoformat()}\n"
        
        # Add to KB repository
        self.kb_repo.update_documentation(
            self.kb_name,
            "map",
            map_name,
            content
        )
        
        return map_name
    
    def _generate_doc_id(self, file_path):
        """Generate a unique document ID."""
        file_str = str(file_path.absolute())
        timestamp = datetime.now().isoformat()
        hash_input = f"{file_str}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _create_metadata(self, file_path, doc_id):
        """Create metadata for a document."""
        stats = file_path.stat()
        
        metadata = {
            "doc_id": doc_id,
            "title": file_path.stem,
            "filename": file_path.name,
            "original_path": str(file_path.absolute()),
            "file_type": file_path.suffix.lower()[1:] if file_path.suffix else "unknown",
            "content_type": self._determine_content_type(file_path),
            "creation_time": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modification_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "file_size": stats.st_size,
            "processing_time": datetime.now().isoformat(),
            "knowledge_base": self.kb_name,
            "version": "1.0"
        }
        
        # Add specific metadata for code files
        if self._is_code_file(file_path):
            code_metadata = self._extract_code_metadata(file_path)
            metadata.update(code_metadata)
            
        return metadata
    
    def _determine_content_type(self, file_path):
        """Determine the content type of a file."""
        suffix = file_path.suffix.lower()
        
        if self._is_code_file(file_path):
            return "code"
        elif self._is_markdown_file(file_path):
            return "markdown"
        elif self._is_image_file(file_path):
            return "image"
        elif suffix in ['.txt', '.csv', '.json', '.yaml', '.yml']:
            return "text"
        elif suffix in ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']:
            return "document"
        else:
            return "other"
    
    def _is_code_file(self, file_path):
        """Check if a file is a code file."""
        code_extensions = [
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.go', 
            '.rb', '.php', '.swift', '.kt', '.rs', '.sh', '.ps1', '.bat'
        ]
        return file_path.suffix.lower() in code_extensions
    
    def _is_markdown_file(self, file_path):
        """Check if a file is a markdown file."""
        markdown_extensions = ['.md', '.markdown']
        return file_path.suffix.lower() in markdown_extensions
    
    def _is_image_file(self, file_path):
        """Check if a file is an image file."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        return file_path.suffix.lower() in image_extensions
    
    def _process_code_file(self, file_path):
        """Process a code file, extracting comments and structure."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
            
        # Convert code to markdown with syntax highlighting
        language = file_path.suffix.lower()[1:]  # Remove the dot
        markdown = f"# Code File: {file_path.name}\n\n"
        markdown += f"```{language}\n{code}\n```\n\n"
        
        # Add extracted documentation
        doc_comments = self._extract_doc_comments(code, language)
        if doc_comments:
            markdown += "## Documentation Comments\n\n"
            markdown += doc_comments
            
        # Add citation info
        markdown += "\n\n## Citation Information\n\n"
        markdown += f"- File: `{file_path.name}`\n"
        markdown += f"- Language: {language}\n"
        markdown += f"- Last Modified: {datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()}\n"
            
        return markdown
    
    def _process_markdown_file(self, file_path):
        """Process a markdown file, preserving structure but handling images."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            markdown = f.read()
            
        # Convert embedded images to text if image processor is available
        if self.image_processor:
            markdown = self._convert_markdown_images(markdown, file_path)
            
        # Add citation info
        markdown += "\n\n## Citation Information\n\n"
        markdown += f"- Document: `{file_path.name}`\n"
        markdown += f"- Last Modified: {datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()}\n"
        
        return markdown
    
    def _convert_markdown_images(self, markdown, file_path):
        """Convert markdown image references to text descriptions."""
        # Pattern to find markdown images: ![alt text](image.jpg)
        img_pattern = r'!\[(.*?)\]\((.*?)\)'
        
        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # If it's a relative path, resolve it relative to the markdown file
            if not img_path.startswith(('http://', 'https://')):
                img_full_path = file_path.parent / img_path
                if img_full_path.exists() and self.image_processor:
                    description = self.image_processor.extract_text(img_full_path)
                    return f"[Image: {alt_text or img_path} - {description}]"
            
            # Return original alt text if we can't process the image
            return f"[Image: {alt_text or img_path}]"
        
        return re.sub(img_pattern, replace_image, markdown)
    
    def _extract_code_metadata(self, file_path):
        """Extract metadata from code files."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
            
        language = file_path.suffix.lower()[1:]  # Remove the dot
        
        metadata = {
            "language": language,
            "line_count": len(code.splitlines()),
        }
        
        # Extract functions/classes depending on language
        if language == 'py':
            # Simple regex-based extraction for Python
            functions = re.findall(r'def\s+(\w+)\s*\(', code)
            classes = re.findall(r'class\s+(\w+)\s*[:(]', code)
            metadata["functions"] = functions
            metadata["classes"] = classes
        elif language in ['js', 'ts']:
            # Simple regex for JavaScript/TypeScript
            functions = re.findall(r'function\s+(\w+)\s*\(', code)
            methods = re.findall(r'(\w+)\s*\([^)]*\)\s*\{', code)
            classes = re.findall(r'class\s+(\w+)', code)
            metadata["functions"] = functions + methods
            metadata["classes"] = classes
            
        return metadata
    
    def _extract_doc_comments(self, code, language):
        """Extract documentation comments from code."""
        doc_comments = ""
        
        if language == 'py':
            # Extract Python docstrings - simplistic approach
            docstrings = re.findall(r'"""(.*?)"""', code, re.DOTALL)
            doc_comments = "\n\n".join(docstring.strip() for docstring in docstrings)
        elif language in ['js', 'ts', 'java', 'c', 'cpp']:
            # Extract JSDoc style comments
            jsdoc_comments = re.findall(r'/\*\*(.*?)\*/', code, re.DOTALL)
            doc_comments = "\n\n".join(comment.strip() for comment in jsdoc_comments)
            
        return doc_comments
    
    def _convert_to_plain_text(self, content):
        """Convert processed content to plain text for RAG."""
        # Remove markdown formatting
        text = content
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove headers
        text = re.sub(r'#+\s+', '', text)
        
        # Remove links but keep link text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        # Remove bold/italic formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        return text
    
    def _commit_changes(self, commit_message):
        """Commit all changes to the git repository."""
        # Add all files
        self.repo.git.add(all=True)
        
        # Create commit
        self.repo.index.commit(commit_message)


class SimpleImageProcessor:
    """Simple image processor that extracts text from images."""
    
    def extract_text(self, image_path):
        """Extract text from an image. 
        This is a placeholder - in a real implementation, 
        use OCR like Tesseract or a cloud OCR service.
        """
        return f"[Image content from {image_path.name}]"


# Example usage
def main():
    from processor.chunker import SemanticChunker
    
    # Create bulk ingestor
    ingestor = BulkIngestor(
        output_dir="/data/knowledge_base",
        kb_name="technical_docs",
        image_processor=SimpleImageProcessor()
    )
    
    # Process a directory
    processed_files = ingestor.process_directory("/path/to/documents")
    
    # Chunk documents
    chunker = SemanticChunker()
    for doc_id in processed_files:
        ingestor.chunk_document(doc_id, chunker)
    
    # Generate process documentation
    ingestor.generate_process_documentation(
        "Document Processing Workflow",
        "This process describes how documents are ingested, processed, and stored in the knowledge base."
    )
    
    # Generate knowledge map
    ingestor.generate_knowledge_map(
        "Technical Documentation Map",
        processed_files
    )

if __name__ == "__main__":
    main()