#!/usr/bin/env python
"""
Test script to verify the new homepage structure
"""

import os
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required files exist in the new structure"""
    base_dir = Path('/Users/maxrocketman/myproject/MelonMind')
    
    # Test homepage app structure
    homepage_files = [
        'apps/homepage/__init__.py',
        'apps/homepage/apps.py', 
        'apps/homepage/models.py',
        'apps/homepage/views.py',
        'apps/homepage/urls.py',
        'apps/homepage/templates/homepage/home.html'
    ]
    
    print("Testing homepage app structure:")
    all_good = True
    for file_path in homepage_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_good = False
    
    # Test settings configuration
    settings_path = base_dir / 'config/settings.py'
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            content = f.read()
            if "'apps.homepage'," in content:
                print("✅ Homepage app registered in settings")
            else:
                print("❌ Homepage app not registered in settings")
                all_good = False
    else:
        print("❌ Settings file not found")
        all_good = False
    
    # Test URL configuration
    urls_path = base_dir / 'config/urls.py'
    if urls_path.exists():
        with open(urls_path, 'r') as f:
            content = f.read()
            if "path('', include('apps.homepage.urls'))" in content:
                print("✅ Homepage URLs configured correctly")
            else:
                print("❌ Homepage URLs not configured correctly")
                all_good = False
            
            if "path('api/', include('apps.common.urls'))" in content:
                print("✅ Common API URLs maintained")
            else:
                print("❌ Common API URLs not found")
                all_good = False
    else:
        print("❌ URLs file not found")
        all_good = False
    
    # Test common app cleanup
    common_views_path = base_dir / 'apps/common/views.py'
    if common_views_path.exists():
        with open(common_views_path, 'r') as f:
            content = f.read()
            if "def home_page(" not in content:
                print("✅ Homepage code removed from common app")
            else:
                print("❌ Homepage code still present in common app")
                all_good = False
    else:
        print("❌ Common views file not found")
        all_good = False
    
    return all_good

def test_imports():
    """Test that the modules can be imported"""
    print("\nTesting imports:")
    
    try:
        sys.path.insert(0, '/Users/maxrocketman/myproject/MelonMind')
        
        # Test homepage app import
        from apps.homepage import views
        print("✅ Homepage views import successful")
        
        # Test common app import  
        from apps.common import views as common_views
        print("✅ Common views import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing new homepage structure...\n")
    
    structure_ok = test_project_structure()
    imports_ok = test_imports()
    
    if structure_ok and imports_ok:
        print("\n🎉 All tests passed! The new structure is ready.")
        print("\nNew URL structure:")
        print("- http://127.0.0.1:8000/ - Homepage (HTML)")
        print("- http://127.0.0.1:8000/health/ - Homepage health check")
        print("- http://127.0.0.1:8000/api/ - API root (JSON)")
        print("- http://127.0.0.1:8000/api/health/ - API health check")
        print("- http://127.0.0.1:8000/api/agents/ - Agents API")
        print("- http://127.0.0.1:8000/api/knowledge/ - Knowledge base API")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)