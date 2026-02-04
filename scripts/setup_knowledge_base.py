#!/usr/bin/env python
"""
初始化知识库脚本
用于创建初始的知识库条目和配置
"""

import os
import django
from django.conf import settings

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.knowledge_base.models import KnowledgeEntry
from django.contrib.auth.models import User


def create_initial_knowledge_entries():
    """创建初始知识库条目"""
    
    # 创建管理员用户（如果不存在）
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
        print("创建管理员用户: admin/admin123")
    
    # 初始知识条目数据
    initial_entries = [
        {
            'title': 'Cisco 路由器基本配置指南',
            'category': 'configuration',
            'content': '''
# Cisco 路由器基本配置指南

## 基本设置步骤

1. **进入全局配置模式**
```
Router> enable
Router# configure terminal
```

2. **设置主机名**
```
Router(config)# hostname MyRouter
```

3. **配置管理IP**
```
MyRouter(config)# interface GigabitEthernet0/0
MyRouter(config-if)# ip address 192.168.1.1 255.255.255.0
MyRouter(config-if)# no shutdown
```

4. **保存配置**
```
MyRouter# copy running-config startup-config
```
            ''',
            'tags': 'cisco,router,configuration,network',
            'source': 'Cisco 官方文档',
            'created_by': admin_user,
            'is_published': True
        },
        {
            'title': '网络故障排除标准流程',
            'category': 'troubleshooting',
            'content': '''
# 网络故障排除标准流程

## 1. 问题识别阶段
- 收集用户反馈
- 确认故障现象
- 记录故障时间

## 2. 信息收集阶段
- 检查网络连通性
- 查看设备状态
- 分析日志信息

## 3. 假设验证阶段
- 制定可能原因假设
- 逐一验证假设
- 缩小问题范围

## 4. 解决方案实施
- 制定解决方案
- 执行修复操作
- 验证修复效果

## 5. 文档记录
- 记录故障详情
- 更新知识库
- 总结经验教训
            ''',
            'tags': 'troubleshooting,fault,process,network',
            'source': '内部运维手册',
            'created_by': admin_user,
            'is_published': True
        },
        {
            'title': '网络安全最佳实践',
            'category': 'security',
            'content': '''
# 网络安全最佳实践

## 访问控制
- 实施最小权限原则
- 定期审查用户权限
- 使用强密码策略

## 设备安全
- 及时更新固件
- 关闭不必要的服务
- 配置访问控制列表

## 监控与审计
- 启用日志记录
- 定期安全扫描
- 建立告警机制

## 备份策略
- 定期配置备份
- 测试恢复流程
- 异地存储备份
            ''',
            'tags': 'security,best-practices,network,cybersecurity',
            'source': '行业标准指南',
            'created_by': admin_user,
            'is_published': True
        }
    ]
    
    # 创建知识条目
    created_count = 0
    for entry_data in initial_entries:
        entry, created = KnowledgeEntry.objects.get_or_create(
            title=entry_data['title'],
            defaults=entry_data
        )
        if created:
            created_count += 1
            print(f"创建知识条目: {entry.title}")
    
    print(f"总共创建了 {created_count} 个初始知识条目")


def setup_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    
    # 这里可以添加数据库初始化逻辑
    # 例如创建必要的表、索引等
    
    print("数据库初始化完成")


if __name__ == '__main__':
    print("开始初始化 MelonMind 知识库...")
    
    try:
        setup_database()
        create_initial_knowledge_entries()
        print("知识库初始化完成！")
    except Exception as e:
        print(f"初始化过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()