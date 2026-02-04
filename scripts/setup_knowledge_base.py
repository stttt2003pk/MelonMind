#!/usr/bin/env python
"""
Initialize knowledge base script
Used to create initial knowledge base entries and configuration
"""

import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.knowledge_base.models import KnowledgeEntry
from django.contrib.auth.models import User


def create_initial_knowledge_entries():
    """Create initial knowledge base entries"""
    
    # Create admin user (if not exists)
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("Created admin user: admin/admin123")
    
    # Initial knowledge entry data
    initial_entries = [
        {
            'title': 'Cisco Router Basic Configuration Guide',
            'category': 'configuration',
            'content': '''
# Cisco Router Basic Configuration Guide

## Basic Setup Steps

1. **Enter Global Configuration Mode**
```
Router> enable
Router# configure terminal
```

2. **Set Hostname**
```
Router(config)# hostname MyRouter
```

3. **Configure Management IP**
```
MyRouter(config)# interface GigabitEthernet0/0
MyRouter(config-if)# ip address 192.168.1.1 255.255.255.0
MyRouter(config-if)# no shutdown
```

4. **Save Configuration**
```
MyRouter# copy running-config startup-config
```
            ''',
            'tags': 'cisco,router,configuration,network',
            'source': 'Cisco Official Documentation',
            'created_by': admin_user,
            'is_published': True
        },
        {
            'title': 'Standard Network Troubleshooting Process',
            'category': 'troubleshooting',
            'content': '''
# Standard Network Troubleshooting Process

## 1. Problem Identification Phase
- Collect user feedback
- Confirm fault symptoms
- Record fault time

## 2. Information Gathering Phase
- Check network connectivity
- View device status
- Analyze log information

## 3. Hypothesis Verification Phase
- Develop possible cause hypotheses
- Verify hypotheses one by one
- Narrow down problem scope

## 4. Solution Implementation
- Develop solution
- Execute repair operations
- Verify repair effectiveness

## 5. Documentation
- Record fault details
- Update knowledge base
- Summarize lessons learned
            ''',
            'tags': 'troubleshooting,fault,process,network',
            'source': 'Internal Operations Manual',
            'created_by': admin_user,
            'is_published': True
        },
        {
            'title': 'Network Security Best Practices',
            'category': 'security',
            'content': '''
# Network Security Best Practices

## Access Control
- Implement principle of least privilege
- Regularly review user permissions
- Use strong password policies

## Device Security
- Update firmware promptly
- Disable unnecessary services
- Configure access control lists

## Monitoring and Auditing
- Enable log recording
- Regular security scanning
- Establish alert mechanisms

## Backup Strategy
- Regular configuration backups
- Test recovery procedures
- Off-site backup storage
            ''',
            'tags': 'security,best-practices,network,cybersecurity',
            'source': 'Industry Standard Guidelines',
            'created_by': admin_user,
            'is_published': True
        }
    ]
    
    # Create knowledge entries
    created_count = 0
    for entry_data in initial_entries:
        entry, created = KnowledgeEntry.objects.get_or_create(
            title=entry_data['title'],
            defaults=entry_data
        )
        if created:
            created_count += 1
            print(f"Created knowledge entry: {entry.title}")
    
    print(f"Total {created_count} initial knowledge entries created")


def setup_database():
    """Initialize database"""
    print("Initializing database...")
    
    # Database initialization logic can be added here
    # For example, creating necessary tables, indexes, etc.
    
    print("Database initialization completed")


if __name__ == '__main__':
    print("Starting MelonMind knowledge base initialization...")
    
    try:
        setup_database()
        create_initial_knowledge_entries()
        print("Knowledge base initialization completed!")
    except Exception as e:
        print(f"Error occurred during initialization: {str(e)}")
        import traceback
        traceback.print_exc()