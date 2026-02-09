"""
Custom test runner to handle PostgreSQL test database creation issues
"""
from django.test.runner import DiscoverRunner
from django.core.management import call_command
from django.db import connections
from django.test.utils import setup_test_environment, teardown_test_environment


class CustomTestRunner(DiscoverRunner):
    """
    Custom test runner that completely bypasses Django's problematic
    test database creation process for PostgreSQL
    """
    
    def setup_databases(self, **kwargs):
        """
        Setup test databases with full control over the process
        """
        # Store original database settings
        old_names = {}
        mirrors = {}
        
        # For each database connection
        for alias in connections:
            connection = connections[alias]
            
            # Store original database name
            old_names[alias] = connection.settings_dict['NAME']
            
            # Create test database name
            test_db_name = f"test_{old_names[alias]}"
            connection.settings_dict['NAME'] = test_db_name
            
            # Check if test database exists, create if not
            with connection._nodb_cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    [test_db_name]
                )
                if not cursor.fetchone():
                    cursor.execute(
                        f'CREATE DATABASE "{test_db_name}" '
                        f'WITH TEMPLATE = template0 '
                        f'ENCODING = "UTF8"'
                    )
            
            # Close current connection and reconnect to test database
            connection.close()
            connection.connect()
            
            # Apply all migrations
            call_command('migrate', database=alias, verbosity=0)
        
        return old_names
    
    def teardown_databases(self, old_config, **kwargs):
        """
        Clean up test databases
        """
        for alias, old_name in old_config.items():
            connection = connections[alias]
            test_db_name = connection.settings_dict['NAME']
            
            # Close connection
            connection.close()
            
            # Restore original database name
            connection.settings_dict['NAME'] = old_name
            
            # Drop test database
            with connection._nodb_cursor() as cursor:
                cursor.execute(
                    f'DROP DATABASE IF EXISTS "{test_db_name}"'
                )
