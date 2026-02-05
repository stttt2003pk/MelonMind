#!/usr/bin/env python3
"""
CASI参考指南测试运行脚本
"""

import os
import sys
import subprocess
import argparse

def run_test(test_file, verbose=False):
    """运行指定的测试文件"""
    cmd = [
        'poetry', 'run', 'python', '-m', 'pytest',
        test_file,
        '-v' if verbose else '',
        '--tb=short',
        '-s'
    ]
    
    # 移除空字符串
    cmd = [arg for arg in cmd if arg]
    
    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='运行CASI参考指南测试')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--real', action='store_true', help='运行真实环境测试')
    parser.add_argument('--api-only', action='store_true', help='只运行API流程测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--use-real-embedding', action='store_true', help='使用真实的embedding服务（而非mock）')
    parser.add_argument('--embedding-only', action='store_true', help='只运行真实embedding服务测试')
    
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    
    if args.real:
        os.environ['RUN_REAL_PDF_TESTS'] = 'true'
        print("⚠ 启用真实环境测试（需要配置Milvus和embedding服务）")
    
    # 控制是否使用真实embedding服务
    if args.use_real_embedding:
        os.environ['USE_MOCK_EMBEDDING'] = 'false'
        print("⚠ 启用真实embedding服务")
        # 检查API密钥
        qwen_key = os.environ.get('QWEN_API_KEY')
        openai_key = os.environ.get('OPENAI_API_KEY')
        if not qwen_key and not openai_key:
            print("⚠ 警告: 未找到QWEN_API_KEY或OPENAI_API_KEY环境变量")
            print("   请设置相应的API密钥以使用真实embedding服务")
            print("   当前测试将继续使用mock服务")
            os.environ['USE_MOCK_EMBEDDING'] = 'true'
        else:
            if qwen_key:
                print(f"   ✓ 使用Qwen API服务 (key: {qwen_key[:8]}...{qwen_key[-4:]})")
            if openai_key:
                print(f"   ✓ 使用OpenAI API服务 (key: {openai_key[:8]}...{openai_key[-4:]})")
    else:
        os.environ['USE_MOCK_EMBEDDING'] = 'true'
        print("✓ 使用mock embedding服务（默认）")
    
    test_dir = os.path.dirname(__file__)
    
    if args.api_only:
        test_files = [os.path.join(test_dir, 'test_casi_api_flow.py')]
    elif args.integration:
        test_files = [os.path.join(test_dir, 'test_casi_guide_integration.py')]
    elif args.embedding_only:
        test_files = [os.path.join(test_dir, 'test_casi_real_embedding.py')]
    else:
        # 运行所有测试
        test_files = [
            os.path.join(test_dir, 'test_casi_api_flow.py'),
            os.path.join(test_dir, 'test_casi_guide_integration.py')
        ]
        # 如果启用了真实embedding测试，也包含embedding测试
        if args.use_real_embedding:
            test_files.append(os.path.join(test_dir, 'test_casi_real_embedding.py'))
    
    print("开始运行 CASI 参考指南测试...")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_files)
    
    for test_file in test_files:
        print(f"\n运行测试文件: {os.path.basename(test_file)}")
        if run_test(test_file, args.verbose):
            success_count += 1
            print(f"✓ {os.path.basename(test_file)} 测试通过")
        else:
            print(f"✗ {os.path.basename(test_file)} 测试失败")
    
    print("\n" + "=" * 60)
    print(f"测试总结: {success_count}/{total_count} 个测试文件通过")
    
    if success_count == total_count:
        print("🎉 所有测试都成功通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())