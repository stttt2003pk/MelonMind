# 知识库测试说明

本文档介绍了 MelonMind 项目中知识库相关的测试文件及其用途。

## 测试文件概览

### 1. test_document_stats.py
- **功能**: 测试文档统计 API 的各种场景
- **测试内容**:
  - 空数据库场景下的统计返回
  - 有数据情况下的统计准确性
  - 边界条件测试（全部完成、各种混合状态等）
- **验证指标**:
  - 总文档数
  - 已处理文档数
  - 正在处理文档数
  - 失败文档数
  - 已上传文档数

### 2. test_frontend_integration.py
- **功能**: 模拟前端如何与文档统计 API 进行交互
- **测试内容**:
  - 前端 API 调用模拟
  - 不同应用场景下的数据处理
  - 错误处理机制
- **模拟场景**:
  - 新安装系统（无文档）
  - 活跃系统（大量文档）
  - 高失败率情况
  - 处理队列情况

## 测试执行方式

### 运行单个测试文件
```bash
# 文档统计测试
python -m pytest tests/test_knowledge_base/test_document_stats.py -v

# 前端集成测试
python -m pytest tests/test_knowledge_base/test_frontend_integration.py -v
```

### 运行全部知识库测试
```bash
python -m pytest tests/test_knowledge_base/ -v
```

## 设计理念

这些测试遵循以下原则：
1. **隔离性**: 使用 mock 对象避免对真实数据库的依赖
2. **全面性**: 覆盖正常和异常情况
3. **可读性**: 测试名称和断言清晰明了
4. **可维护性**: 便于理解和修改

## 维护说明

- 当修改文档统计 API 时，请相应更新测试用例
- 添加新的文档状态时，需要扩展测试场景
- 保持测试与实际业务逻辑的一致性