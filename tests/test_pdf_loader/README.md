# PDF Loader 测试说明

## 测试目录结构

```
tests/test_pdf_loader/
├── test_casi/                   # CASI参考指南专用测试
│   ├── test_casi_working_edge.py # CASI Working Edge 查询测试
│   └── pdf/                     # 测试PDF文件目录
└── README.md                    # 本文件
```

## 运行测试

### CASI参考指南测试
```bash
# 直接运行测试脚本
python tests/test_pdf_loader/test_casi/test_casi_working_edge.py

# 或使用Django测试运行器
python manage.py test tests.test_pdf_loader.test_casi.test_casi_working_edge -v 2
```

## 测试功能

### CASI Working Edge 测试
- 测试CASO_RefGuide.pdf文件的完整处理流程
- 验证"working edge"关键词的向量搜索功能
- 包含PDF上传、状态检查、向量搜索等端到端测试
- 支持13.9MB大型PDF文件处理
- 返回相似度排序的搜索结果

## 测试环境要求

### 环境变量
```bash
export DJANGO_SETTINGS_MODULE=config.settings
```

### 注意事项
1. 测试会在Django测试数据库中运行，不影响生产数据
2. 测试完成后会自动清理临时文件