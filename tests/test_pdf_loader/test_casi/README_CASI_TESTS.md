# CASI 参考指南测试套件

这个测试套件专门用于测试 CASI 参考指南 PDF 文件的完整处理流程，包括上传、处理、向量化和查询。

## 测试文件说明

### 1. `test_casi_api_flow.py` - API流程测试
- 测试从PDF上传到向量查询的完整API调用流程
- 包含边界情况和错误处理测试
- 使用mock数据避免依赖外部服务

### 2. `test_casi_guide_integration.py` - 集成测试
- 更全面的集成测试，包含多个测试阶段
- 支持真实环境测试（需要配置Milvus和embedding服务）
- 详细的测试步骤和验证

### 3. `run_casi_tests.py` - 测试运行脚本
- 方便的命令行测试运行工具
- 支持不同的测试模式选择

## 运行测试

### 基本运行
```bash
# 运行所有测试
poetry run python tests/test_pdf_loader/run_casi_tests.py

# 详细输出
poetry run python tests/test_pdf_loader/run_casi_tests.py --verbose

# 只运行API流程测试
poetry run python tests/test_pdf_loader/run_casi_tests.py --api-only

# 只运行集成测试
poetry run python tests/test_pdf_loader/run_casi_tests.py --integration
```

### 真实环境测试
```bash
# 运行真实环境测试（需要配置Milvus）
poetry run python tests/test_pdf_loader/run_casi_tests.py --real
```

### 直接运行单个测试文件
```bash
# 运行API流程测试
poetry run python -m pytest tests/test_pdf_loader/test_casi_api_flow.py -v -s

# 运行集成测试
poetry run python -m pytest tests/test_pdf_loader/test_casi_guide_integration.py -v -s
```

## 测试流程说明

测试按照以下顺序执行：

1. **PDF上传测试**
   - 验证PDF文件成功上传到系统
   - 检查返回的文档ID和基本信息

2. **处理状态检查**
   - 查询文档处理状态
   - 验证状态变化（pending → processing → completed）

3. **等待处理完成**
   - 模拟等待后台处理完成
   - 在真实环境中会实际等待处理结束

4. **向量搜索测试**
   - 使用查询语句："3 core components in CASI"
   - 验证搜索结果的相关性和准确性
   - 测试多个相关的查询变体

5. **结果验证**
   - 验证数据库记录
   - 检查API端点可用性
   - 验证Milvus连接状态

## 预期测试结果

### 成功场景
```
✓ PDF上传成功，文档ID: 123
✓ 当前处理状态: completed  
✓ 执行向量搜索...
✓ 搜索完成，找到 3 个相关结果
✓ 数据库验证通过
```

### 搜索结果示例
```
查询: '3 core components in CASI'
结果 1: 相似度 0.92
        页码 3
        内容: The CASI system comprises three core architectural components...

结果 2: 相似度 0.87  
        页码 7
        内容: Three fundamental components define the CASI framework...
```

## 环境要求

### 基础测试（Mock模式）
- Python 3.8+
- Django 4.2+
- pytest
- 无需外部服务

### 真实环境测试
除了基础要求外，还需要：
- Milvus数据库服务运行中
- 配置有效的embedding服务（如OpenAI或Qwen）
- 正确的数据库连接配置

## 故障排除

### 常见问题

1. **PDF文件找不到**
   ```
   AssertionError: 测试PDF文件不存在: /path/to/CASI_RefGuide.pdf
   ```
   解决：确认PDF文件在正确的路径下

2. **数据库连接失败**
   ```
   django.db.utils.OperationalError: could not connect to server
   ```
   解决：检查数据库服务是否运行，配置是否正确

3. **Milvus连接失败**
   ```
   ConnectionError: 无法连接到Milvus数据库
   ```
   解决：确认Milvus服务运行，网络连接正常

4. **测试超时**
   ```
   ⚠ 超时：处理未在预期时间内完成
   ```
   解决：增加等待时间，或检查后台处理服务状态

### 调试建议

1. 使用 `-s` 参数查看详细输出
2. 使用 `--verbose` 获取更多信息
3. 检查Django日志输出
4. 验证各服务组件状态

## 扩展测试

可以根据需要添加更多测试场景：

- 不同类型的PDF文件测试
- 大文件处理性能测试  
- 并发上传测试
- 错误恢复测试
- 不同查询语句的效果对比

## 测试数据清理

测试会自动清理创建的测试数据，但如果测试中断，可以手动清理：

```python
# 在Django shell中运行
from apps.pdfloader.models import PDFDocument, PDFChunk
from apps.mulvesdb.models import MulvesConnection

# 清理测试数据
PDFDocument.objects.filter(title__contains='Test').delete()
PDFChunk.objects.filter(document__title__contains='Test').delete()
MulvesConnection.objects.filter(name__contains='Test').delete()
```