#!/usr/bin/env python3
"""
向量元数据追踪功能测试运行器
统一执行所有相关的测试用例
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_python_test(test_file, description):
    """运行单个Python测试文件"""
    print(f"\n{'='*60}")
    print(f"正在执行: {description}")
    print(f"测试文件: {test_file}")
    print(f"{'='*60}")
    
    try:
        # 构建命令
        cmd = [sys.executable, str(test_file)]
        
        # 执行测试
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

def run_django_test(test_label, description):
    """运行Django测试"""
    print(f"\n{'='*60}")
    print(f"正在执行: {description}")
    print(f"{'='*60}")
    
    try:
        # 构建Django测试命令
        cmd = [
            sys.executable, 
            str(project_root / 'manage.py'), 
            'test', 
            test_label,
            '--verbosity=2',
            '--keepdb'  # 保持测试数据库以提高速度
        ]
        
        # 执行测试
        result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR输出:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 执行Django测试时发生错误: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='向量元数据追踪测试运行器')
    parser.add_argument('--suite', choices=['unit', 'integration', 'api', 'all'], 
                       default='all', help='选择测试套件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    print("🚀 向量元数据追踪功能测试运行器")
    print("=" * 60)
    
    # 测试结果统计
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # 确定要运行的测试
    test_suites = []
    
    if args.suite in ['unit', 'all']:
        test_suites.extend([
            (str(project_root / 'tests/test_mulvesdb/test_vector_metadata_tracking.py'), '向量元数据追踪单元测试'),
            (str(project_root / 'tests/test_mulvesdb/test_comprehensive_metadata_tracking.py'), '向量元数据综合测试')
        ])
    
    if args.suite in ['integration', 'all']:
        test_suites.extend([
            (str(project_root / 'tests/test_mulvesdb/test_metadata_integration.py'), '向量元数据集成测试')
        ])
    
    if args.suite in ['api', 'all']:
        test_suites.extend([
            (str(project_root / 'tests/test_mulvesdb/test_metadata_api.py'), '向量元数据API测试')
        ])
    
    # 执行测试
    for test_file, description in test_suites:
        test_path = project_root / test_file
        if test_path.exists():
            success = run_python_test(test_path, description)
            results['total'] += 1
            if success:
                results['passed'] += 1
                print(f"✅ {description} - 通过")
            else:
                results['failed'] += 1
                print(f"❌ {description} - 失败")
        else:
            print(f"⚠️  测试文件不存在: {test_file}")
            results['total'] += 1
            results['failed'] += 1
    
    # 显示总结
    print("\n" + "=" * 60)
    print("📊 测试执行总结")
    print("=" * 60)
    print(f"总测试数: {results['total']}")
    print(f"通过: {results['passed']}")
    print(f"失败: {results['failed']}")
    print(f"成功率: {results['passed']/results['total']*100:.1f}%" if results['total'] > 0 else "无测试执行")
    
    if results['failed'] == 0:
        print("\n🎉 所有测试通过！向量元数据追踪功能工作正常。")
        return 0
    else:
        print(f"\n❌ {results['failed']} 个测试失败，请检查上述输出。")
        return 1

if __name__ == '__main__':
    exit(main())