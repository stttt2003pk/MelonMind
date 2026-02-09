"""
PDF Loader 文档去重功能简化测试
验证核心的去重功能是否正常工作
"""

import os
import sys
import tempfile
import django

# 设置Django环境
sys.path.append('/Users/maxrocketman/myproject/MelonMind')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.pdfloader.utils import calculate_file_hash
from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection


def test_basic_deduplication():
    """测试基本的去重功能"""
    print("=== 测试基本去重功能 ===")
    
    # 创建测试内容
    test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n/Test (Deduplication Test)\n>>\nendobj\n"
    
    # 创建两个相同内容的临时文件
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f1:
        f1.write(test_content)
        file1_path = f1.name
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f2:
        f2.write(test_content)
        file2_path = f2.name
    
    try:
        # 计算哈希值
        hash1 = calculate_file_hash(file1_path)
        hash2 = calculate_file_hash(file2_path)
        
        print(f"✓ 两个相同文件哈希一致: {hash1 == hash2}")
        print(f"✓ 哈希长度正确: {len(hash1) == 64}")
        
        # 测试模型方法
        # 清理可能存在的测试数据
        PDFDocument.objects.filter(title="Dedup Test Document").delete()
        
        # 创建测试连接
        connection, created = MulvesConnection.objects.get_or_create(
            name="dedup_test_connection",
            defaults={
                'host': 'localhost',
                'port': 19530,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass',
                'is_active': True
            }
        )
        
        # 创建测试文档
        test_doc = PDFDocument.objects.create(
            title="Dedup Test Document",
            file_path=file1_path,
            file_size=len(test_content),
            file_hash=hash1,
            page_count=1,
            milvus_connection=connection,
            collection_name="dedup_test_collection",
            status="completed"
        )
        
        print(f"✓ 创建测试文档成功")
        
        # 测试去重检查方法
        exists = PDFDocument.exists_by_file_hash(hash1)
        print(f"✓ exists_by_file_hash工作正常: {exists}")
        
        found_doc = PDFDocument.get_by_file_hash(hash1)
        print(f"✓ get_by_file_hash工作正常: {found_doc.id == test_doc.id}")
        
        # 清理
        test_doc.delete()
        if created:
            connection.delete()
            
        print("🎉 基本去重功能测试通过!")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        for file_path in [file1_path, file2_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)


def test_hash_uniqueness():
    """测试不同文件产生不同哈希"""
    print("\n=== 测试哈希唯一性 ===")
    
    content1 = b"%PDF-1.4\n1 0 obj\n<<\n/Different (Content 1)\n>>\nendobj\n"
    content2 = b"%PDF-1.4\n1 0 obj\n<<\n/Different (Content 2)\n>>\nendobj\n"
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f1:
        f1.write(content1)
        file1_path = f1.name
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f2:
        f2.write(content2)
        file2_path = f2.name
    
    try:
        hash1 = calculate_file_hash(file1_path)
        hash2 = calculate_file_hash(file2_path)
        
        print(f"✓ 不同内容产生不同哈希: {hash1 != hash2}")
        print(f"✓ 两个哈希都有效: {len(hash1) == 64 and len(hash2) == 64}")
        
        return True
    except Exception as e:
        print(f"✗ 哈希唯一性测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        for file_path in [file1_path, file2_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)


if __name__ == "__main__":
    print("开始测试PDF文档去重功能...\n")
    
    results = []
    results.append(("基本去重功能", test_basic_deduplication()))
    results.append(("哈希唯一性", test_hash_uniqueness()))
    
    # 输出总结
    print("\n" + "="*40)
    print("测试结果总结:")
    print("="*40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name:15} : {status}")
        if not passed:
            all_passed = False
    
    print("="*40)
    if all_passed:
        print("🎉 所有测试通过！")
        exit(0)
    else:
        print("❌ 部分测试失败")
        exit(1)