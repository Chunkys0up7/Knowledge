from ingestor.smart_ingestor import SmartIngestor
from processor.chunker import SemanticChunker
from processor.vector_optimizer import VectorOptimizer
from storage.document_store import DocumentStore
from search.hybrid_search import HybridSearch
from rag.rag_system import RAGSystem
from security.abac_engine import ABACEngine
from security.audit_trail import AuditTrail

class KnowledgeSystem:
    """Main entry point for the Knowledge Management System.
    
    Integrates all the components into a cohesive system:
    - Document ingestion and processing
    - Storage and indexing
    - Search and retrieval
    - RAG capabilities
    - Security and audit
    """
    
    def __init__(self, config=None):
        # Initialize system with optional configuration
        self.config = config or {}
        
        # Initialize components
        self.ingestor = SmartIngestor()
        self.chunker = SemanticChunker(
            max_tokens=self.config.get('chunking', {}).get('max_tokens', 512),
            overlap=self.config.get('chunking', {}).get('overlap', 64)
        )
        self.vector_optimizer = VectorOptimizer()
        self.document_store = DocumentStore()
        self.search_engine = HybridSearch()
        self.rag_system = RAGSystem(retriever=self.search_engine)
        self.access_control = ABACEngine()
        self.audit_trail = AuditTrail()
    
    def ingest_document(self, file_path, metadata=None):
        """Ingest a document from a file path."""
        # Process document
        content = self.ingestor.process(file_path)
        
        # Create chunks
        chunks = self.chunker.chunk(content)
        
        # Create vector representations
        vectors = [self.vector_optimizer.optimize(chunk) for chunk in chunks]
        
        # Store document and chunks
        doc_metadata = metadata or {}
        doc_id = self.document_store.store_document(content, doc_metadata)
        
        # Log the ingestion
        self.audit_trail.log_access(
            user_id=doc_metadata.get('user_id', 'system'),
            document_id=doc_id,
            action='create',
            details={'file_path': file_path}
        )
        
        return doc_id
    
    def search(self, query, user=None):
        """Search for documents matching the query."""
        # Authorize the search
        if user and not self._authorize_search(user, query):
            return {'error': 'Unauthorized'}
        
        # Perform search
        results = self.search_engine.search(query)
        
        # Log the search
        if user:
            self.audit_trail.log_access(
                user_id=user.get('id', 'anonymous'),
                document_id='search:' + query,
                action='search',
                details={'query': query, 'result_count': len(results)}
            )
        
        return results
    
    def generate_response(self, query, user=None):
        """Generate a response to a query using RAG."""
        # Authorize the query
        if user and not self._authorize_search(user, query):
            return {'error': 'Unauthorized'}
        
        # Generate response
        response = self.rag_system.generate_response(query)
        
        # Log the generation
        if user:
            self.audit_trail.log_access(
                user_id=user.get('id', 'anonymous'),
                document_id='query:' + query,
                action='generate',
                details={'query': query}
            )
        
        return response
    
    def _authorize_search(self, user, query):
        """Authorize a search request."""
        # This is a placeholder implementation
        # In practice, would implement more sophisticated authorization
        return True

# Example usage
def main():
    # Create system
    system = KnowledgeSystem()
    
    # Example query
    response = system.generate_response("What are the retention rules for financial documents?")
    print(response)

if __name__ == "__main__":
    main()
