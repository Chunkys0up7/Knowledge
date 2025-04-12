"""
Configuration management for the Knowledge Management System.

This module handles loading and merging configuration from multiple sources:
1. Default configuration
2. Environment variables
3. Configuration files (YAML)
4. Command-line arguments

All system components should use this module to access configuration values.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Setup logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    # Base paths
    'output_dir': '/data/knowledge_base',
    'kb_base_dir': '/data/knowledge_bases',
    'temp_dir': '/tmp/kb_uploads',
    
    # Company information
    'company': {
        'name': 'Your Company',
        'logo_url': None,  # Path or URL to company logo
        'color_primary': '#2196F3',
        'color_secondary': '#FF5722',
        'domain': 'example.com',
        'contact_email': 'support@example.com'
    },
    
    # Web UI configuration
    'web_ui': {
        'enabled': True,
        'host': '0.0.0.0',
        'port': 5000,
        'debug': False,
        'title': 'Knowledge Management System',
        'session_secret': 'change-this-in-production',
        'max_upload_size_mb': 1024,  # 1GB
        'allowed_file_types': [
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.go',
            '.rb', '.php', '.swift', '.kt', '.rs', '.sh', '.ps1', '.bat',
            '.md', '.markdown', '.txt', '.csv', '.json', '.yaml', '.yml',
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
        ]
    },
    
    # API configuration
    'api': {
        'enabled': True,
        'require_auth': False,  # Set to True in production
        'auth_provider': 'none',  # 'none', 'jwt', 'oauth2'
        'jwt_secret': 'change-this-in-production',
        'token_expiry_hours': 24,
        'rate_limit': {
            'enabled': True,
            'requests_per_minute': 60
        },
        'cors': {
            'enabled': True,
            'allow_origins': ['*'],
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE'],
        }
    },
    
    # Document processing
    'processing': {
        'batch_size': 50,
        'polling_interval': 300,  # 5 minutes
        'max_workers': 4,  # Maximum concurrent worker threads
        'chunk_size': 10,  # Process files in chunks of 10
        'memory_limit_mb': 1024,  # 1GB memory limit (soft limit)
        'git_auto_commit': True,
    },
    
    # Chunking configuration
    'chunking': {
        'max_tokens': 512,
        'overlap': 64,
        'min_chunk_size': 100,  # Minimum characters per chunk
        'respect_boundaries': True,  # Respect semantic boundaries
    },
    
    # Storage configuration
    'storage': {
        'vector_store': {
            'type': 'faiss',  # 'faiss', 'qdrant', 'elastic'
            'path': '/data/knowledge_base/vectors',
            'dimensions': 768,
            'metric': 'cosine',
        },
        'git_store': {
            'enabled': True,
            'lfs_enabled': False,  # Git LFS for large files
            'auto_push': False,  # Auto push to remote
            'remote_url': None,
            'username': None,
            'token': None,
        }
    },
    
    # Image processing
    'image_processing': {
        'enabled': True,
        'ocr': True,
        'ocr_engine': 'tesseract',  # 'tesseract', 'google', 'azure'
        'ocr_api_key': None,
        'image_description': True,
    },
    
    # Search configuration
    'search': {
        'hybrid_search': True,  # Combine vector and keyword search
        'vector_weight': 0.7,
        'keyword_weight': 0.3,
        'max_results': 10,
        'min_score': 0.5,  # Minimum similarity score (0-1)
    },
    
    # Security configuration
    'security': {
        'abac_enabled': False,  # Attribute-based access control
        'audit_trail': True,  # Log all access
        'pii_detection': False,  # Personally identifiable information detection
        'sensitive_info_detection': False,  # Detect sensitive information
    },
    
    # Logging configuration
    'logging': {
        'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'file': 'knowledge_system.log',
        'max_size_mb': 10,
        'backup_count': 3,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    },
    
    # Watch directories for automated processing
    'watch_directories': [],
}


class Config:
    """Configuration manager for the Knowledge Management System."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize configuration from default values and specified sources.
        
        Args:
            config_path: Optional path to a YAML configuration file
        """
        self._config = DEFAULT_CONFIG.copy()
        
        # Load configuration from environment variables
        self._load_from_env()
        
        # Load configuration from file
        if config_path:
            self._load_from_file(config_path)
        else:
            # Try to find config in default locations
            self._try_default_config_locations()
            
        # Create required directories
        self._ensure_directories()
        
        logger.debug(f"Configuration initialized: {self._config}")
        
    def _load_from_env(self):
        """Load configuration values from environment variables.
        
        Environment variables should be prefixed with KB_
        Examples:
            KB_OUTPUT_DIR=/path/to/output
            KB_WEB_UI_PORT=8080
            KB_COMPANY_NAME="Acme Corp"
        """
        prefix = 'KB_'
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix):].lower()
                
                # Handle nested keys (e.g., KB_WEB_UI_PORT)
                parts = config_key.split('_')
                
                # Parse boolean values
                if value.lower() in ['true', 'yes', '1']:
                    value = True
                elif value.lower() in ['false', 'no', '0']:
                    value = False
                # Parse numeric values
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                    value = float(value)
                
                # Apply the configuration
                self._set_nested_config(parts, value)
                
        logger.debug("Loaded configuration from environment variables")
        
    def _set_nested_config(self, key_parts: List[str], value: Any):
        """Set a value in the nested configuration dictionary.
        
        Args:
            key_parts: List of nested key parts
            value: Value to set
        """
        if not key_parts:
            return
            
        config = self._config
        for part in key_parts[:-1]:
            if part not in config:
                config[part] = {}
            elif not isinstance(config[part], dict):
                config[part] = {}
            config = config[part]
            
        config[key_parts[-1]] = value
    
    def _load_from_file(self, config_path: Union[str, Path]):
        """Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return
            
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                
            if not user_config:
                logger.warning(f"Empty configuration file: {config_path}")
                return
                
            # Merge configuration
            self._merge_config(self._config, user_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge two configuration dictionaries.
        
        Args:
            base: Base configuration dictionary (modified in place)
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if (
                key in base and 
                isinstance(base[key], dict) and 
                isinstance(value, dict)
            ):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _try_default_config_locations(self):
        """Try to load configuration from default locations."""
        config_paths = [
            'config.yaml',
            'conf/config.yaml',
            '/etc/knowledge-system/config.yaml',
            os.path.expanduser('~/.config/knowledge-system/config.yaml'),
            os.path.expanduser('~/.knowledge-system/config.yaml'),
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                self._load_from_file(path)
                break
    
    def _ensure_directories(self):
        """Create required directories if they don't exist."""
        directories = [
            self._config['output_dir'],
            self._config['kb_base_dir'],
            self._config['temp_dir'],
            self._config['storage']['vector_store']['path'],
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
            except Exception as e:
                logger.warning(f"Could not create directory {directory}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key (dot notation for nested keys)
            default: Default value to return if key is not found
            
        Returns:
            Configuration value or default
        """
        parts = key.split('.')
        config = self._config
        
        for part in parts:
            if isinstance(config, dict) and part in config:
                config = config[part]
            else:
                return default
                
        return config
    
    def set(self, key: str, value: Any):
        """Set a configuration value by key.
        
        Args:
            key: Configuration key (dot notation for nested keys)
            value: Value to set
        """
        parts = key.split('.')
        self._set_nested_config(parts, value)
    
    def update(self, config: Dict[str, Any]):
        """Update configuration with values from a dictionary.
        
        Args:
            config: Dictionary of configuration values
        """
        self._merge_config(self._config, config)
    
    @property
    def as_dict(self) -> Dict[str, Any]:
        """Get the full configuration as a dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        return self._config.copy()
    
    def save(self, path: Optional[Union[str, Path]] = None):
        """Save the current configuration to a file.
        
        Args:
            path: Path to save the configuration file
        """
        if not path:
            path = 'config.yaml'
            
        path = Path(path)
        
        try:
            with open(path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {path}: {e}")


# Global configuration instance
_config_instance = None

def get_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Get the global configuration instance.
    
    Args:
        config_path: Optional path to a configuration file
        
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_path)
        
    return _config_instance