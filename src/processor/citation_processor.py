import re
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

class CitationProcessor:
    """Processes documents to ensure proper citation information is preserved.
    
    Citation data includes:
    - Document ID
    - Page/section/line information
    - Document title/name
    - Author information if available
    - Publication date if available
    - Version information if available
    - Repository location
    """
    
    def __init__(self, output_dir="/data/knowledge_base"):
        self.output_dir = Path(output_dir)
        self.citation_dir = self.output_dir / "citations"
        self.citation_dir.mkdir(parents=True, exist_ok=True)
        
    def process_document(self, document_path, doc_id, metadata):
        """Process a document and generate citation information."""
        document_path = Path(document_path)
        
        # Create a citation object
        citation = {
            "doc_id": doc_id,
            "filename": document_path.name,
            "title": metadata.get("title", document_path.stem),
            "path": str(document_path),
            "created_at": metadata.get("creation_time", datetime.now().isoformat()),
            "processed_at": datetime.now().isoformat(),
            "content_type": metadata.get("content_type", "unknown"),
            "file_type": metadata.get("file_type", "unknown"),
            "author": metadata.get("author", "Unknown"),
            "version": metadata.get("version", "1.0"),
            "repository": str(self.output_dir),
            "citation_format": self._get_citation_format(document_path, metadata),
            "sections": []
        }
        
        # Process document based on type
        if self._is_code_file(document_path):
            citation["sections"] = self._process_code_sections(document_path)
        elif self._is_markdown_file(document_path):
            citation["sections"] = self._process_markdown_sections(document_path)
        elif metadata.get("file_type") == "pdf":
            citation["sections"] = self._process_pdf_sections(document_path, metadata)
        else:
            citation["sections"] = self._process_generic_sections(document_path)
            
        # Save citation file
        citation_file = self.citation_dir / f"{doc_id}_citation.json"
        with open(citation_file, 'w') as f:
            json.dump(citation, f, indent=2)
            
        return citation
    
    def generate_chunk_citations(self, chunks, doc_id):
        """Generate citation information for each chunk."""
        citation_file = self.citation_dir / f"{doc_id}_citation.json"
        
        if not citation_file.exists():
            return []
            
        with open(citation_file, 'r') as f:
            citation = json.load(f)
            
        chunk_citations = []
        
        for i, chunk in enumerate(chunks):
            # Generate chunk ID
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Find which section(s) this chunk belongs to
            sections = self._find_chunk_sections(chunk, citation["sections"])
            
            # Create chunk citation
            chunk_citation = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "title": citation.get("title", "Unknown"),
                "author": citation.get("author", "Unknown"),
                "version": citation.get("version", "1.0"),
                "sections": sections,
                "citation_text": self._format_citation(citation, sections),
                "repository_link": f"{citation['repository']}/processed/{doc_id}.md"
            }
            
            chunk_citations.append(chunk_citation)
            
        return chunk_citations
    
    def _get_citation_format(self, document_path, metadata):
        """Determine the citation format for a document."""
        content_type = metadata.get("content_type", "unknown")
        
        if content_type == "code":
            return "code"
        elif content_type == "markdown":
            return "markdown"
        elif metadata.get("file_type") == "pdf":
            return "pdf"
        else:
            return "generic"
    
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
    
    def _process_code_sections(self, file_path):
        """Process a code file into sections for citation."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code_lines = f.readlines()
            
        sections = []
        
        # Find classes
        class_pattern = r'^\s*class\s+(\w+)'
        for i, line in enumerate(code_lines):
            matches = re.search(class_pattern, line)
            if matches:
                class_name = matches.group(1)
                # Find end of class (naive approach)
                end_line = len(code_lines)
                for j in range(i + 1, len(code_lines)):
                    if re.match(r'^\s*class\s+', code_lines[j]):
                        end_line = j
                        break
                        
                sections.append({
                    "type": "class",
                    "name": class_name,
                    "start_line": i + 1,
                    "end_line": end_line,
                    "content_hash": self._hash_content(''.join(code_lines[i:end_line])),
                    "citation_key": f"{file_path.stem}:class:{class_name}"
                })
        
        # Find functions
        function_pattern = r'^\s*def\s+(\w+)'
        for i, line in enumerate(code_lines):
            matches = re.search(function_pattern, line)
            if matches:
                function_name = matches.group(1)
                # Find end of function (naive approach)
                end_line = len(code_lines)
                for j in range(i + 1, len(code_lines)):
                    if re.match(r'^\s*def\s+', code_lines[j]) or re.match(r'^\s*class\s+', code_lines[j]):
                        end_line = j
                        break
                        
                sections.append({
                    "type": "function",
                    "name": function_name,
                    "start_line": i + 1,
                    "end_line": end_line,
                    "content_hash": self._hash_content(''.join(code_lines[i:end_line])),
                    "citation_key": f"{file_path.stem}:function:{function_name}"
                })
        
        # If no sections found, create a generic section
        if not sections:
            sections.append({
                "type": "file",
                "name": file_path.stem,
                "start_line": 1,
                "end_line": len(code_lines),
                "content_hash": self._hash_content(''.join(code_lines)),
                "citation_key": file_path.stem
            })
            
        return sections
    
    def _process_markdown_sections(self, file_path):
        """Process a markdown file into sections for citation."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            md_lines = f.readlines()
            
        sections = []
        
        # Find headers
        current_section = {"type": "header", "level": 0, "name": file_path.stem, 
                           "start_line": 1, "lines": []}
        
        for i, line in enumerate(md_lines):
            header_match = re.match(r'^(#{1,6})\s+(.*?)(?:\s+#{1,6})?$', line)
            if header_match:
                # Save previous section if it had content
                if current_section["lines"]:
                    current_section["end_line"] = i
                    current_section["content_hash"] = self._hash_content(''.join(current_section["lines"]))
                    current_section["citation_key"] = f"{file_path.stem}:{current_section['level']}:{current_section['name']}"
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(header_match.group(1))
                name = header_match.group(2).strip()
                current_section = {
                    "type": "header",
                    "level": level,
                    "name": name,
                    "start_line": i + 1,
                    "lines": [line],
                    "citation_key": f"{file_path.stem}:{level}:{name}"
                }
            else:
                current_section["lines"].append(line)
        
        # Save final section
        if current_section["lines"]:
            current_section["end_line"] = len(md_lines)
            current_section["content_hash"] = self._hash_content(''.join(current_section["lines"]))
            sections.append(current_section.copy())
            
        # If no sections found, create a generic section
        if not sections:
            sections.append({
                "type": "file",
                "name": file_path.stem,
                "start_line": 1,
                "end_line": len(md_lines),
                "content_hash": self._hash_content(''.join(md_lines)),
                "citation_key": file_path.stem
            })
            
        return sections
    
    def _process_pdf_sections(self, file_path, metadata):
        """Process PDF sections based on metadata (since we can't read PDFs directly)."""
        sections = []
        
        # Use metadata for sections if available
        if "pages" in metadata:
            for i, page_info in enumerate(metadata["pages"]):
                sections.append({
                    "type": "page",
                    "name": f"Page {i+1}",
                    "page_number": i + 1,
                    "citation_key": f"{file_path.stem}:page:{i+1}"
                })
        else:
            # Create a generic section for the whole document
            sections.append({
                "type": "document",
                "name": file_path.stem,
                "citation_key": file_path.stem
            })
            
        return sections
    
    def _process_generic_sections(self, file_path):
        """Process a generic file into sections."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # Create a generic section
            return [{
                "type": "file",
                "name": file_path.stem,
                "content_hash": self._hash_content(content),
                "citation_key": file_path.stem
            }]
        except:
            # File may not be readable as text
            return [{
                "type": "file",
                "name": file_path.stem,
                "citation_key": file_path.stem
            }]
    
    def _find_chunk_sections(self, chunk, sections):
        """Find which sections a chunk belongs to."""
        # Simple implementation: check if chunk content is in section
        matching_sections = []
        
        for section in sections:
            if "content_hash" in section:
                # Check if chunk content is a subset of section content
                if self._is_content_subset(chunk, section):
                    matching_section = {
                        "type": section["type"],
                        "name": section["name"],
                        "citation_key": section["citation_key"]
                    }
                    
                    # Add line numbers if available
                    if "start_line" in section:
                        matching_section["start_line"] = section["start_line"]
                    if "end_line" in section:
                        matching_section["end_line"] = section["end_line"]
                        
                    matching_sections.append(matching_section)
        
        # If no matching sections, return a generic reference to the document
        if not matching_sections and sections:
            return [{
                "type": "document",
                "name": sections[0].get("name", "Unknown"),
                "citation_key": sections[0].get("citation_key", "unknown")
            }]
            
        return matching_sections
    
    def _is_content_subset(self, chunk, section):
        """Check if a chunk's content is a subset of a section's content."""
        # For simplicity, we're using a basic string search
        # In a real implementation, this would be more sophisticated
        if "lines" in section:
            section_content = ''.join(section["lines"])
            return chunk in section_content
        return False
    
    def _format_citation(self, citation, sections):
        """Format a citation string based on document type and sections."""
        if not sections:
            return f"{citation.get('title', 'Unknown Document')} ({citation.get('version', '1.0')})"
            
        # Format based on document type
        if citation.get("citation_format") == "code":
            return self._format_code_citation(citation, sections)
        elif citation.get("citation_format") == "markdown":
            return self._format_markdown_citation(citation, sections)
        elif citation.get("citation_format") == "pdf":
            return self._format_pdf_citation(citation, sections)
        else:
            return self._format_generic_citation(citation, sections)
    
    def _format_code_citation(self, citation, sections):
        """Format a citation for code documents."""
        parts = [f"{citation.get('title', 'Unknown')}"]
        
        if sections:
            section = sections[0]  # Use first section
            if section["type"] == "class":
                parts.append(f"Class {section['name']}")
            elif section["type"] == "function":
                parts.append(f"Function {section['name']}")
                
            if "start_line" in section and "end_line" in section:
                parts.append(f"Lines {section['start_line']}-{section['end_line']}")
                
        parts.append(f"Version {citation.get('version', '1.0')}")
        
        return ", ".join(parts)
    
    def _format_markdown_citation(self, citation, sections):
        """Format a citation for markdown documents."""
        parts = [f"{citation.get('title', 'Unknown')}"]
        
        if sections:
            section = sections[0]  # Use first section
            if section["type"] == "header":
                header_prefix = "#" * section.get("level", 1)
                parts.append(f"{header_prefix} {section['name']}")
                
        if citation.get("author", "Unknown") != "Unknown":
            parts.append(f"by {citation['author']}")
            
        parts.append(f"Version {citation.get('version', '1.0')}")
        
        return ", ".join(parts)
    
    def _format_pdf_citation(self, citation, sections):
        """Format a citation for PDF documents."""
        parts = [f"{citation.get('title', 'Unknown')}"]
        
        if citation.get("author", "Unknown") != "Unknown":
            parts.append(f"by {citation['author']}")
            
        if sections:
            section = sections[0]  # Use first section
            if section["type"] == "page" and "page_number" in section:
                parts.append(f"Page {section['page_number']}")
                
        return ", ".join(parts)
    
    def _format_generic_citation(self, citation, sections):
        """Format a generic citation."""
        parts = [f"{citation.get('title', 'Unknown')}"]
        
        if citation.get("author", "Unknown") != "Unknown":
            parts.append(f"by {citation['author']}")
            
        parts.append(f"Version {citation.get('version', '1.0')}")
        
        return ", ".join(parts)
    
    def _hash_content(self, content):
        """Create a hash of content for comparison."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()