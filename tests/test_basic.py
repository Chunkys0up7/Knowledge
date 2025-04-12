import unittest
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestor.smart_ingestor import SmartIngestor
from src.processor.chunker import SemanticChunker
from src.processor.vector_optimizer import VectorOptimizer, TextCleaner
from src.storage.document_store import DocumentStore
from src.storage.retention_policy import RetentionPolicy
from src.search.hybrid_search import HybridSearch
from src.rag.rag_system import RAGSystem
from src.security.abac_engine import ABACEngine
from src.security.audit_trail import AuditTrail
from src.main import KnowledgeSystem


class TestComponents(unittest.TestCase):
    """Test all components of the Knowledge Management System."""
    
    def test_retention_policy(self):
        """Test that retention policy works correctly."""
        # Setup
        policy_dict = {
            'retention_rules': {
                'financial': {
                    'default': '7yrs',
                    'exceptions': {
                        'SOX': '10yrs'
                    }
                },
                'healthcare': {
                    'hipaa': '6yrs',
                    'emr': 'patient_lifetime'
                }
            }
        }
        
        policy = RetentionPolicy(policy_dict=policy_dict)
        
        # Test
        financial_period = policy.get_retention_period('financial')
        sox_period = policy.get_retention_period('financial', 'SOX')
        hipaa_period = policy.get_retention_period('healthcare', 'hipaa')
        
        # Assert
        self.assertEqual(financial_period, '7yrs')
        self.assertEqual(sox_period, '10yrs')
        self.assertEqual(hipaa_period, '6yrs')
    
    def test_text_cleaner(self):
        """Test that text cleaner preserves basic text."""
        # Setup
        cleaner = TextCleaner()
        
        # Test
        text = "This is a test document."
        cleaned = cleaner.remove_artifacts(text)
        
        # Assert
        self.assertEqual(cleaned, text)
    
    def test_vector_optimizer(self):
        """Test that vector optimizer produces vectors of expected dimension."""
        # Setup
        optimizer = VectorOptimizer()
        
        # Test
        text = "This is a test document."
        vector = optimizer.optimize(text)
        
        # Assert
        self.assertIsInstance(vector, list)
        self.assertEqual(len(vector), 768)  # Default dimension in our placeholder
    
    def test_knowledge_system_initialization(self):
        """Test that the KnowledgeSystem initializes without errors."""
        # Setup & Test
        system = KnowledgeSystem()
        
        # Assert
        self.assertIsInstance(system.ingestor, SmartIngestor)
        self.assertIsInstance(system.chunker, SemanticChunker)
        self.assertIsInstance(system.vector_optimizer, VectorOptimizer)
        self.assertIsInstance(system.document_store, DocumentStore)
        self.assertIsInstance(system.search_engine, HybridSearch)
        self.assertIsInstance(system.rag_system, RAGSystem)
        self.assertIsInstance(system.access_control, ABACEngine)
        self.assertIsInstance(system.audit_trail, AuditTrail)


if __name__ == '__main__':
    unittest.main()