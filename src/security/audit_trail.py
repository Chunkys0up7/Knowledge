import time
import uuid
import hashlib

class AuditTrail:
    """Implements audit logging for document access and modifications.
    
    Audit Log Schema:
    - timestamp: ISO 8601
    - user: UUIDv4
    - document: SHA256 hash
    - action: CRUD + search
    - risk_score: 0-100
    """
    
    def __init__(self, storage_backend=None):
        self.storage_backend = storage_backend  # Will be a database or file system
    
    def log_access(self, user_id, document_id, action, details=None):
        """Log an access to a document."""
        audit_entry = self._create_audit_entry(user_id, document_id, action, details)
        return self._store_audit_entry(audit_entry)
    
    def _create_audit_entry(self, user_id, document_id, action, details=None):
        """Create an audit entry object."""
        # Calculate risk score based on action and details
        risk_score = self._calculate_risk_score(action, details)
        
        # Create the audit entry
        entry = {
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            'user': str(user_id),
            'document': self._hash_document_id(document_id),
            'action': action,
            'risk_score': risk_score
        }
        
        if details:
            entry['details'] = details
            
        return entry
    
    def _hash_document_id(self, document_id):
        """Create a SHA256 hash of the document ID."""
        return hashlib.sha256(str(document_id).encode()).hexdigest()
    
    def _calculate_risk_score(self, action, details=None):
        """Calculate a risk score based on the action and details."""
        # This is a placeholder implementation
        # In practice, would implement a more sophisticated risk scoring system
        risk_scores = {
            'view': 10,
            'search': 5,
            'create': 20,
            'update': 30,
            'delete': 50
        }
        
        return risk_scores.get(action, 0)
    
    def _store_audit_entry(self, entry):
        """Store the audit entry in the storage backend."""
        # This is a placeholder implementation
        if self.storage_backend:
            return self.storage_backend.store(entry)
        return str(uuid.uuid4())  # Return a fake entry ID if no storage backend
