#!/usr/bin/env python3
"""
依赖检查脚本
验证项目所需的所有Python包是否正确安装
"""

import sys
import importlib
from typing import Dict, List, Tuple

# 项目必需的依赖包
REQUIRED_PACKAGES = {
    # 核心框架
    'django': 'Django Web框架',
    'rest_framework': 'Django REST Framework',
    'psycopg2': 'PostgreSQL数据库驱动',
    
    # 异步支持
    'asyncpg': 'PostgreSQL异步驱动',
    
    # AI相关
    'langchain': 'LangChain框架',
    'langchain_core': 'LangChain核心组件',
    'langchain_community': 'LangChain社区组件',
    'langgraph': 'LangGraph流程编排',
    
    # 工具库
    'dotenv': '环境变量管理',
    'corsheaders': 'CORS支持',
    'celery': '异步任务队列',
    'redis': 'Redis客户端',
    
    # 开发工具
    'pytest': '测试框架',
    'pytest_django.plugin': 'Django测试插件',
    'drf_yasg': 'API文档生成',
}

# 可选依赖包
OPTIONAL_PACKAGES = {
    'pytest_asyncio': '异步测试支持',
    'black': '代码格式化工具',
    'flake8': '代码质量检查',
    'mypy': '类型检查工具',
    'IPython': '增强的Python交互环境',
}


def check_package(package_name: str, package_desc: str) -> Tuple[bool, str]:
    """检查单个包是否安装"""
    try:
        importlib.import_module(package_name)
        module = sys.modules[package_name]
        version = getattr(module, '__version__', 'unknown')
        return True, f"✓ {package_desc} ({package_name} v{version})"
    except ImportError:
        return False, f"✗ {package_desc} ({package_name}) - 未安装"


def main():
    """主检查函数"""
    print("🔍 检查项目依赖安装状态...")
    print("=" * 50)
    
    # 检查必需依赖
    print("\n📋 必需依赖检查:")
    required_issues = []
    for package, desc in REQUIRED_PACKAGES.items():
        success, message = check_package(package, desc)
        print(f"  {message}")
        if not success:
            required_issues.append(package)
    
    # 检查可选依赖
    print("\n🔧 可选依赖检查:")
    optional_missing = []
    for package, desc in OPTIONAL_PACKAGES.items():
        success, message = check_package(package, desc)
        print(f"  {message}")
        if not success:
            optional_missing.append(package)
    
    # 输出总结
    print("\n" + "=" * 50)
    if required_issues:
        print("❌ 发现问题:")
        print("以下必需依赖未安装:")
        for package in required_issues:
            print(f"  - {package}")
        print("\n请运行以下命令安装缺失的依赖:")
        print("  poetry install")
        sys.exit(1)
    else:
        print("✅ 所有必需依赖均已正确安装!")
        
        if optional_missing:
            print(f"\n💡 提示: 以下可选依赖未安装:")
            for package in optional_missing:
                print(f"  - {package} ({OPTIONAL_PACKAGES[package]})")
            print("这些不影响核心功能，但建议安装以获得更好的开发体验")
        else:
            print("🎉 所有依赖都已完美安装!")


if __name__ == "__main__":
    main()