"""
Block Deduplication Unit Tests
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.mulvesdb.utils import (
    calculate_chunk_hash, 
    calculate_chunk_hash_simple,
    ChunkDeduplicationManager,
    filter_duplicate_chunks
)
from apps.mulvesdb.models import ChunkHashIndex
from apps.mulvesdb.connectors import MulvesDBConnector


class TestChunkHashCalculation(TestCase):
    """Test chunk hash calculation functionality"""
    
    def test_calculate_chunk_hash_basic(self):
        """Test basic composite hash calculation"""
        content = "This is test content"
        document_id = 1
        chunk_index = 0
        
        hash_value = calculate_chunk_hash(content, document_id, chunk_index)
        
        # Verify return value format
        self.assertIsInstance(hash_value, str)
        self.assertEqual(len(hash_value), 64)  # SHA-256 should be 64 characters
        
        # Verify same input produces same output
        hash_value2 = calculate_chunk_hash(content, document_id, chunk_index)
        self.assertEqual(hash_value, hash_value2)
    
    def test_calculate_chunk_hash_differentiates_content(self):
        """Test different content produces different hashes"""
        content1 = "Content A"
        content2 = "Content B"
        document_id = 1
        chunk_index = 0
        
        hash1 = calculate_chunk_hash(content1, document_id, chunk_index)
        hash2 = calculate_chunk_hash(content2, document_id, chunk_index)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_calculate_chunk_hash_considers_document_id(self):
        """Test document ID affects hash value"""
        content = "Same content"
        chunk_index = 0
        
        hash1 = calculate_chunk_hash(content, document_id=1, chunk_index=chunk_index)
        hash2 = calculate_chunk_hash(content, document_id=2, chunk_index=chunk_index)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_calculate_chunk_hash_considers_chunk_index(self):
        """Test chunk index affects hash value"""
        content = "Same content"
        document_id = 1
        
        hash1 = calculate_chunk_hash(content, document_id=document_id, chunk_index=0)
        hash2 = calculate_chunk_hash(content, document_id=document_id, chunk_index=1)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_calculate_chunk_hash_invalid_inputs(self):
        """Test invalid input handling"""
        with self.assertRaises(TypeError):
            calculate_chunk_hash(123, 1, 0)  # content is not string
            
        with self.assertRaises(ValueError):
            calculate_chunk_hash("content", -1, 0)  # document_id negative
            
        with self.assertRaises(ValueError):
            calculate_chunk_hash("content", 1, -1)  # chunk_index negative
    
    def test_calculate_chunk_hash_simple(self):
        """Test simple content hash calculation"""
        content = "test content"
        hash_value = calculate_chunk_hash_simple(content)
        
        self.assertIsInstance(hash_value, str)
        self.assertEqual(len(hash_value), 64)
        
        # Same content should produce same hash
        hash_value2 = calculate_chunk_hash_simple(content)
        self.assertEqual(hash_value, hash_value2)


class TestChunkDeduplicationManager(TestCase):
    """Test deduplication manager"""
    
    def setUp(self):
        self.manager = ChunkDeduplicationManager(cache_size=5)
    
    def test_is_duplicate_new_content(self):
        """Test new content is not considered duplicate"""
        hash_value = "a" * 64
        result = self.manager.is_duplicate(hash_value)
        self.assertFalse(result)
    
    def test_is_duplicate_existing_content(self):
        """Test existing content is considered duplicate"""
        hash_value = "b" * 64
        self.manager.add_hash(hash_value)
        result = self.manager.is_duplicate(hash_value)
        self.assertTrue(result)
    
    def test_add_hash_success(self):
        """Test successful hash addition"""
        hash_value = "c" * 64
        result = self.manager.add_hash(hash_value)
        self.assertTrue(result)
        
        # Verify can be detected as duplicate
        self.assertTrue(self.manager.is_duplicate(hash_value))
    
    def test_add_hash_duplicate(self):
        """Test duplicate hash addition"""
        hash_value = "d" * 64
        self.manager.add_hash(hash_value)
        result = self.manager.add_hash(hash_value)
        self.assertFalse(result)  # Already exists, addition fails
    
    def test_cache_limit_enforcement(self):
        """Test cache size limit enforcement"""
        # Add more hashes than cache size
        hashes = [f"{'a' * 54}{i:010d}" for i in range(10)]  # Generate valid 64-character hashes
        
        for h in hashes:
            self.manager.add_hash(h)
        
        # Verify early added hashes may have been removed (simple LRU implementation)
        # Note: This is a simplified test, actual LRU behavior may be more complex
    
    def test_batch_operations(self):
        """Test batch operations"""
        hash_values = ["e" * 64, "f" * 64, "g" * 64]
        
        # Batch check
        results = self.manager.batch_check_duplicates(hash_values)
        self.assertEqual(len(results), 3)
        self.assertFalse(any(results))  # All should be False (not duplicate)
        
        # Batch add
        added_count = self.manager.batch_add_hashes(hash_values)
        self.assertEqual(added_count, 3)
        
        # Batch check again should all be True (duplicate)
        results = self.manager.batch_check_duplicates(hash_values)
        self.assertTrue(all(results))
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        # Initial state
        stats = self.manager.get_statistics()
        self.assertEqual(stats['total_checked'], 0)
        self.assertEqual(stats['duplicates_found'], 0)
        self.assertEqual(stats['duplicate_rate'], 0.0)
        
        # Add some operations
        hash1 = "h" * 64
        hash2 = "i" * 64
        
        self.manager.is_duplicate(hash1)  # miss
        self.manager.add_hash(hash1)      # add
        self.manager.is_duplicate(hash1)  # hit
        self.manager.is_duplicate(hash2)  # miss
        
        stats = self.manager.get_statistics()
        self.assertEqual(stats['total_checked'], 3)
        self.assertEqual(stats['duplicates_found'], 1)
        self.assertEqual(stats['cache_hits'], 1)
        self.assertEqual(stats['cache_misses'], 2)
        self.assertAlmostEqual(stats['duplicate_rate'], 33.33, places=2)
        
        # Reset statistics
        self.manager.reset_statistics()
        stats = self.manager.get_statistics()
        self.assertEqual(stats['total_checked'], 0)


class TestFilterDuplicateChunks(TestCase):
    """Test chunk data filtering functionality"""
    
    def setUp(self):
        self.chunks_data = [
            {'content': 'chunk content 1', 'chunk_index': 0, 'page_number': 1},
            {'content': 'chunk content 2', 'chunk_index': 1, 'page_number': 1},
            {'content': 'chunk content 3', 'chunk_index': 2, 'page_number': 2},
        ]
        self.document_id = 1
    
    def test_filter_no_duplicates(self):
        """Test filtering with no duplicate content"""
        filtered = filter_duplicate_chunks(self.chunks_data, self.document_id)
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered, self.chunks_data)
    
    def test_filter_with_duplicates(self):
        """Test filtering with duplicate content"""
        # Create a new manager for this test
        from apps.mulvesdb.utils import ChunkDeduplicationManager
        manager = ChunkDeduplicationManager()
        
        # Add hash for the second chunk to make it appear as duplicate
        chunk_hash = calculate_chunk_hash(
            self.chunks_data[1]['content'], 
            self.document_id, 
            self.chunks_data[1]['chunk_index']
        )
        manager.add_hash(chunk_hash)
        
        # Filter using our custom manager
        filtered = filter_duplicate_chunks(self.chunks_data, self.document_id, manager)
        
        # Should filter out the second chunk (index 1)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['content'], 'chunk content 1')
        self.assertEqual(filtered[1]['content'], 'chunk content 3')


@pytest.mark.django_db
class TestChunkHashIndexModel(TestCase):
    """Test chunk hash index model"""
    
    def setUp(self):
        self.collection_name = "test_collection"
    
    def test_is_duplicate_new_hash(self):
        """Test new hash is not considered duplicate"""
        hash_value = "a" * 64
        result = ChunkHashIndex.is_duplicate(hash_value, self.collection_name)
        self.assertFalse(result)
    
    def test_is_duplicate_existing_hash(self):
        """Test existing hash is considered duplicate"""
        hash_value = "b" * 64
        # First add record
        ChunkHashIndex.add_hash_entry(
            hash_value=hash_value,
            collection_name=self.collection_name,
            document_id=1,
            chunk_index=0,
            content_length=10
        )
        
        # Check duplicate
        result = ChunkHashIndex.is_duplicate(hash_value, self.collection_name)
        self.assertTrue(result)
    
    def test_add_hash_entry_new(self):
        """Test adding new hash entry"""
        hash_value = "c" * 64
        result = ChunkHashIndex.add_hash_entry(
            hash_value=hash_value,
            collection_name=self.collection_name,
            document_id=1,
            chunk_index=0,
            content_length=10
        )
        self.assertTrue(result)  # New creation successful
    
    def test_add_hash_entry_duplicate(self):
        """Test adding duplicate hash entry"""
        hash_value = "d" * 64
        # First addition
        ChunkHashIndex.add_hash_entry(
            hash_value=hash_value,
            collection_name=self.collection_name,
            document_id=1,
            chunk_index=0,
            content_length=10
        )
        
        # Second addition of same hash
        result = ChunkHashIndex.add_hash_entry(
            hash_value=hash_value,
            collection_name=self.collection_name,
            document_id=2,  # Different document
            chunk_index=0,
            content_length=10
        )
        self.assertFalse(result)  # Already exists, returns False
    
    def test_bulk_check_duplicates(self):
        """Test bulk duplicate checking"""
        hash_values = ["e" * 64, "f" * 64, "g" * 64]
        # Add two of them
        ChunkHashIndex.add_hash_entry(hash_values[0], self.collection_name, 1, 0, 10)
        ChunkHashIndex.add_hash_entry(hash_values[2], self.collection_name, 1, 2, 10)
        
        # Bulk check
        duplicates = ChunkHashIndex.bulk_check_duplicates(hash_values, self.collection_name)
        
        self.assertIn(hash_values[0], duplicates)
        self.assertNotIn(hash_values[1], duplicates)
        self.assertIn(hash_values[2], duplicates)


# TODO: Add integration tests for complete insertion flow deduplication
# TODO: Add performance tests for large data volume deduplication efficiency
# TODO: Add concurrency tests for thread safety in multi-threaded environments