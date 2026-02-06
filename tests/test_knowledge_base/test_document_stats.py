"""Test cases for knowledge base document statistics API"""

from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from rest_framework.response import Response as DRFResponse
from apps.knowledge_base.views import get_document_stats


from django.test import SimpleTestCase


class TestDocumentStatsAPI(SimpleTestCase):
    """Test the document stats API endpoint without starting Django server"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.factory = RequestFactory()
        
    def test_empty_document_stats(self):
        """Test document stats endpoint with empty database"""
        request = self.factory.get('/api/knowledge/document-stats/')

        with patch('apps.knowledge_base.views.PDFDocument') as mock_pdf_document:
            # Set up mock for empty database
            mock_pdf_document.objects.count.return_value = 0
            mock_pdf_document.objects.filter.return_value.count.return_value = 0

            response = get_document_stats(request)

            # Assertions
            self.assertIsInstance(response, DRFResponse)
            self.assertEqual(response.status_code, 200)

            response_data = response.data
            expected_keys = ['total_documents', 'processed_documents', 'processing_documents', 
                            'failed_documents', 'uploaded_documents']

            for key in expected_keys:
                self.assertIn(key, response_data)
                self.assertIsInstance(response_data[key], int)
                self.assertGreaterEqual(response_data[key], 0)
                self.assertEqual(response_data[key], 0)  # All should be 0 for empty db
    
    def test_populated_document_stats(self):
        """Test document stats endpoint with sample data"""
        request = self.factory.get('/api/knowledge/document-stats/')

        with patch('apps.knowledge_base.views.PDFDocument') as mock_pdf_document:
            # Create different filter mocks
            completed_qs = MagicMock()
            processing_qs = MagicMock()
            failed_qs = MagicMock()
            uploaded_qs = MagicMock()

            completed_qs.count.return_value = 5
            processing_qs.count.return_value = 2
            failed_qs.count.return_value = 1
            uploaded_qs.count.return_value = 3

            # Configure filter method based on status parameter
            def filter_side_effect(**kwargs):
                status = kwargs.get('status')
                if status == 'completed':
                    return completed_qs
                elif status == 'processing':
                    return processing_qs
                elif status == 'failed':
                    return failed_qs
                elif status == 'uploaded':
                    return uploaded_qs
                else:
                    return MagicMock()

            mock_pdf_document.objects.filter.side_effect = filter_side_effect
            mock_pdf_document.objects.count.return_value = 11  # Total count

            response = get_document_stats(request)

            # Get response data
            response_data = response.data

            # Verify data
            self.assertEqual(response_data['total_documents'], 11)
            self.assertEqual(response_data['processed_documents'], 5)
            self.assertEqual(response_data['processing_documents'], 2)
            self.assertEqual(response_data['failed_documents'], 1)
            self.assertEqual(response_data['uploaded_documents'], 3)
    
    def test_real_world_scenario(self):
        """Test with realistic data distribution"""
        request = self.factory.get('/api/knowledge/document-stats/')

        with patch('apps.knowledge_base.views.PDFDocument') as mock_pdf_document:
            # Simulate actual system data distribution
            mock_pdf_document.objects.count.return_value = 25  # 25 total docs

            # Simulate filter returning different counts
            filters = {
                'completed': 15,  # 15 completed
                'processing': 3,  # 3 processing
                'failed': 2,      # 2 failed
                'uploaded': 5     # 5 uploaded waiting
            }

            def side_effect_filter(**kwargs):
                mock_result = MagicMock()
                status = kwargs.get('status')
                if status in filters:
                    mock_result.count.return_value = filters[status]
                else:
                    mock_result.count.return_value = 0
                return mock_result

            mock_pdf_document.objects.filter.side_effect = side_effect_filter

            response = get_document_stats(request)
            response_data = response.data

            # Verify data consistency
            expected_total = sum(filters.values())
            self.assertEqual(response_data['total_documents'], expected_total)
            self.assertEqual(response_data['processed_documents'], filters['completed'])
            self.assertEqual(response_data['processing_documents'], filters['processing'])
            self.assertEqual(response_data['failed_documents'], filters['failed'])
            self.assertEqual(response_data['uploaded_documents'], filters['uploaded'])
    
    def test_edge_case_all_completed(self):
        """Test edge case where all documents are completed"""
        request = self.factory.get('/api/knowledge/document-stats/')

        with patch('apps.knowledge_base.views.PDFDocument') as mock_pdf_document:
            mock_pdf_document.objects.count.return_value = 10
            mock_pdf_document.objects.filter.return_value.count.return_value = 0  # Default 0

            # Only completed status has data
            def side_effect_filter(**kwargs):
                mock_result = MagicMock()
                status = kwargs.get('status')
                if status == 'completed':
                    mock_result.count.return_value = 10
                else:
                    mock_result.count.return_value = 0
                return mock_result

            mock_pdf_document.objects.filter.side_effect = side_effect_filter

            response = get_document_stats(request)
            response_data = response.data

            self.assertEqual(response_data['total_documents'], 10)
            self.assertEqual(response_data['processed_documents'], 10)
            self.assertEqual(response_data['processing_documents'], 0)
            self.assertEqual(response_data['failed_documents'], 0)
            self.assertEqual(response_data['uploaded_documents'], 0)

