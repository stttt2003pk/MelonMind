"""
Simple test to diagnose database issue
"""
from django.test import TestCase

class SimpleTestCase(TestCase):
    def test_basic(self):
        """Basic test that should pass"""
        self.assertEqual(1 + 1, 2)