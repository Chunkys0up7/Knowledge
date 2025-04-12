import yaml

class RetentionPolicy:
    """Implements document retention policies as code.
    
    Based on the YAML policy definition in the specification:
    ```yaml
    retention_rules:
      financial:
        default: 7yrs
        exceptions:
          SOX: 10yrs
      healthcare:
        hipaa: 6yrs
        emr: 'patient_lifetime'
    ```
    """
    
    def __init__(self, policy_file=None, policy_dict=None):
        if policy_file:
            with open(policy_file, 'r') as f:
                self.policy = yaml.safe_load(f)
        elif policy_dict:
            self.policy = policy_dict
        else:
            # Default policy
            self.policy = {
                'retention_rules': {
                    'default': '7yrs'
                }
            }
    
    def get_retention_period(self, document_type, category=None):
        """Get the retention period for a document based on its type and category."""
        rules = self.policy.get('retention_rules', {})
        
        # Check if document type exists in rules
        if document_type in rules:
            type_rules = rules[document_type]
            
            # Check if there's a specific exception for this category
            if category and 'exceptions' in type_rules and category in type_rules['exceptions']:
                return type_rules['exceptions'][category]
            
            # Otherwise return the default for this document type
            if 'default' in type_rules:
                return type_rules['default']
        
        # Fall back to global default
        return rules.get('default', '7yrs')
    
    def is_expired(self, document_metadata):
        """Check if a document has expired based on its metadata and retention policy."""
        # This is a placeholder implementation
        # In practice, would calculate based on document creation date and retention period
        return False
