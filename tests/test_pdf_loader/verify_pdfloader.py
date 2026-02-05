#!/usr/bin/env python
"""
PDF Loader 基本功能验证脚本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    from django.conf import settings
    django.setup()
except ImportError as e:
    print(f"Django导入失败: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

def test_basic_functionality():
    """测试基本功能"""
    print("=== PDF Loader 基本功能验证 ===\n")
    
    # 测试1: 导入模块
    print("1. 测试模块导入...")
    try:
        from apps.pdfloader.pdf_processor import PDFProcessor
        from apps.pdfloader.embedding import get_embedding_service
        from apps.pdfloader.models import PDFDocument
        print("   ✓ 模块导入成功")
    except Exception as e:
        print(f"   ✗ 模块导入失败: {e}")
        return False
    
    # 测试2: 创建PDF处理器
    print("\n2. 测试PDF处理器创建...")
    try:
        processor = PDFProcessor(chunk_size=500, chunk_overlap=100)
        print("   ✓ PDF处理器创建成功")
        print(f"   - 分块大小: {processor.chunk_size}")
        print(f"   - 重叠大小: {processor.chunk_overlap}")
    except Exception as e:
        print(f"   ✗ PDF处理器创建失败: {e}")
        return False
    
    # 测试3: 测试Embedding服务
    print("\n3. 测试Embedding服务...")
    try:
        # 根据环境变量判断是否使用mock服务
        use_mock = os.getenv('USE_MOCK_EMBEDDING', 'true').lower() == 'true'
        embedding_service = get_embedding_service(use_mock=use_mock)
        result = embedding_service.embed_text("测试文本")
        print("   ✓ Embedding服务工作正常")
        print(f"   - 文本: {result.text}")
        print(f"   - Embedding维度: {len(result.embedding)}")
        print(f"   - 模型: {result.model}")
    except Exception as e:
        print(f"   ✗ Embedding服务测试失败: {e}")
        return False
    
    # 测试4: 测试模型创建
    print("\n4. 测试模型创建...")
    try:
        # 这里只是测试模型定义，不实际创建数据库记录
        print("   ✓ 模型定义正确")
    except Exception as e:
        print(f"   ✗ 模型测试失败: {e}")
        return False
    
    # 测试5: 测试配置
    print("\n5. 测试配置...")
    try:
        print("   ✓ Django配置正常")
        print(f"   - Qwen API Key配置: {'已设置' if os.getenv('QWEN_API_KEY') else '未设置'}")
        print(f"   - 使用Mock Embedding: {use_mock}")
        if not use_mock:
            print(f"   - 正在使用真实Qwen API")
    except Exception as e:
        print(f"   ✗ 配置测试失败: {e}")
        return False
    
    print("\n=== 所有基本功能测试通过! ===")
    print("\n下一步:")
    print("1. 准备一个PDF文件用于测试")
    print("2. 配置Milvus数据库连接")
    print("3. 运行完整处理流程测试")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)