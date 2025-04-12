class ABACEngine:
    """Attribute-Based Access Control engine.
    
    Controls access to documents based on user attributes and document metadata.
    """
    
    def authorize(self, user, doc):
        """Authorize access to a document based on user attributes and document metadata."""
        return all([
            self._match_attr(user.get('roles', []), doc.get('access', [])),
            self._check_expiry(doc),
            self._validate_geo(user.get('location'))
        ])
    
    def _match_attr(self, user_roles, doc_access):
        """Check if user roles match document access requirements."""
        # This is a placeholder implementation
        # In practice, would implement more sophisticated role-based access control
        if not doc_access:  # If no access restrictions, allow access
            return True
            
        # Check if any user role is in the document access list
        return any(role in doc_access for role in user_roles)
    
    def _check_expiry(self, doc):
        """Check if document has expired."""
        # This is a placeholder implementation
        return not doc.get('expired', False)
    
    def _validate_geo(self, location):
        """Validate user's geographic location for geo-restricted content."""
        # This is a placeholder implementation
        return True
