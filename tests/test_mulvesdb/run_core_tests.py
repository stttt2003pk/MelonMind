#!/usr/bin/env python3
"""
向量元数据追踪功能快速测试
只运行已验证通过的核心功能测试
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_core_functionality_tests():
    """运行核心功能测试"""
    print("🚀 向量元数据追踪核心功能测试")
    print("=" * 50)
    
    test_file = project_root / 'tests/test_mulvesdb/test_core_metadata_functionality.py'
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 执行测试
        cmd = [sys.executable, str(test_file)]
        result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR输出:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 执行测试时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("开始执行向量元数据追踪核心功能验证...")
    
    success = run_core_functionality_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 核心功能测试全部通过！")
        print("向量元数据追踪功能可以正常使用。")
        return 0
    else:
        print("❌ 核心功能测试失败！")
        print("请检查上述错误信息。")
        return 1

if __name__ == '__main__':
    exit(main())