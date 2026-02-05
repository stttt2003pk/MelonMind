# PDF Loader 测试说明

## 测试目录结构

```
tests/test_pdf_loader/
├── test_core_functionality.py    # 核心功能测试
├── test_integration.py          # 集成测试
├── test_performance.py          # 性能测试
└── README.md                    # 本文件
```

## 运行测试

### 运行所有测试
```bash
cd /Users/maxrocketman/myproject/MelonMind
python -m pytest tests/test_pdf_loader/ -v
```

### 运行特定测试文件
```bash
# 运行核心功能测试
python -m pytest tests/test_pdf_loader/test_core_functionality.py -v

# 运行集成测试
python -m pytest tests/test_pdf_loader/test_integration.py -v

# 运行性能测试
python -m pytest tests/test_pdf_loader/test_performance.py -v
```

### 运行特定测试类或方法
```bash
# 运行特定测试类
python -m pytest tests/test_pdf_loader/test_core_functionality.py::PDFProcessorTest -v

# 运行特定测试方法
python -m pytest tests/test_pdf_loader/test_core_functionality.py::PDFProcessorTest::test_pdf_text_extraction -v
```

## 测试覆盖的功能

### 1. 核心功能测试 (test_core_functionality.py)
- PDF处理器功能测试
- Embedding服务测试
- PDF文档模型测试
- API端点测试

### 2. 集成测试 (test_integration.py)
- 完整PDF处理流程测试
- 向量搜索功能测试
- 处理状态查询测试
- 真实数据处理测试

### 3. 性能测试 (test_performance.py)
- 大文件处理性能测试
- 并发上传测试
- 分块性能测试
- 批量embedding性能测试

## 测试环境要求

### 依赖包
确保安装了以下测试依赖：
```bash
pip install pytest pytest-django pytest-asyncio
```

### 环境变量
测试可能需要以下环境变量：
```bash
export DJANGO_SETTINGS_MODULE=config.settings
export QWEN_API_KEY=your_qwen_api_key  # 如果不使用mock模式
```

## 测试注意事项

1. **Mock服务**: 默认使用Mock Embedding服务进行测试，避免真实的API调用
2. **数据库**: 测试会在Django测试数据库中运行，不会影响生产数据
3. **文件清理**: 测试会自动清理临时文件
4. **异步处理**: 部分测试涉及异步操作，需要pytest-asyncio支持

## 常见问题

### 1. 测试数据库连接失败
确保Django配置正确，并且可以访问测试数据库。

### 2. PDF处理测试失败
检查PyPDF2是否正确安装，以及测试PDF文件是否有效。

### 3. 异步测试超时
某些性能测试可能需要较长时间，可以根据需要调整超时设置。

## 添加新的测试

1. 在相应测试文件中添加新的测试类或方法
2. 遵循现有测试命名约定
3. 使用适当的setUp和tearDown方法
4. 添加必要的mock和fixtures
5. 确保测试覆盖率和性能要求