#!/usr/bin/env python
"""
调试辅助脚本
提供常用的调试功能和测试入口点
"""

import os
import sys
import django
from django.conf import settings

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def debug_model(model_name):
    """调试特定模型"""
    from django.apps import apps
    
    try:
        model = apps.get_model(model_name)
        print(f"Model: {model}")
        print(f"Fields: {[f.name for f in model._meta.fields]}")
        return model
    except LookupError:
        print(f"Model '{model_name}' not found")
        return None

def debug_database():
    """调试数据库连接"""
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"Database version: {version[0]}")
            
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def debug_settings():
    """调试 Django 设置"""
    print("=== Django Settings Debug ===")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"DATABASES: {settings.DATABASES}")
    print(f"INSTALLED_APPS: {settings.INSTALLED_APPS[:5]}...")  # 只显示前5个
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

if __name__ == "__main__":
    print("=== MelonMind Debug Helper ===")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "model":
            if len(sys.argv) > 2:
                debug_model(sys.argv[2])
            else:
                print("Usage: python debug_helper.py model <app.ModelName>")
                
        elif command == "db":
            debug_database()
            
        elif command == "settings":
            debug_settings()
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: model, db, settings")
    else:
        print("Available commands:")
        print("  python debug_helper.py model <app.ModelName>")
        print("  python debug_helper.py db")
        print("  python debug_helper.py settings")