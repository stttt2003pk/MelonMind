#!/usr/bin/env python3
"""
MelonMind Prompt 展示工具
快速查看项目中的各种提示和模板文件
"""

import os
import sys
from pathlib import Path

def show_file_content(file_path, title):
    """显示文件内容"""
    if os.path.exists(file_path):
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        with open(file_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"\n❌ 文件不存在: {file_path}")

def main():
    """主函数"""
    project_root = Path(__file__).parent
    
    print("🍓 MelonMind Prompt 展示工具")
    print("="*60)
    
    # 显示可用的 prompt 文件
    prompt_files = [
        ("README.md", "📖 项目主文档"),
        ("QUICK_START.md", "⚡ 快速开始指南"),
        ("PROMPTS.md", "🔧 常用命令模板"),
        ("DEBUG_HELPER.md", "🐛 调试助手"),
        ("tests/README.md", "🧪 测试说明"),
        ("docs/index.md", "📚 完整文档索引")
    ]
    
    print("\n可用的文档文件:")
    for i, (file_path, description) in enumerate(prompt_files, 1):
        full_path = project_root / file_path
        status = "✅" if full_path.exists() else "❌"
        print(f"{i}. {status} {description} ({file_path})")
    
    # 交互式选择查看
    while True:
        try:
            choice = input("\n请输入要查看的文件编号 (输入 q 退出): ").strip()
            
            if choice.lower() == 'q':
                print("👋 再见!")
                break
                
            choice_num = int(choice)
            if 1 <= choice_num <= len(prompt_files):
                file_path, description = prompt_files[choice_num - 1]
                full_path = project_root / file_path
                show_file_content(str(full_path), f"{description} - {file_path}")
            else:
                print("❌ 无效的选择，请输入 1-{} 之间的数字".format(len(prompt_files)))
                
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break

if __name__ == "__main__":
    main()