# 知识库测试

此目录包含知识库相关功能的测试用例。

## 测试文件说明

- `test_document_stats.py` - 文档统计 API 的单元测试
- `test_frontend_integration.py` - 前端集成测试，模拟前端如何与文档统计 API 交互
- `test_mulves.py` - Mulves 客户端连接和功能测试

## 测试覆盖范围

- 文档统计 API 的各种场景测试
- 前端与后端 API 的集成验证
- 错误处理和边界情况测试
- 不同文档状态（已完成、处理中、失败、已上传）的统计验证

## 运行测试

要运行此目录下的所有测试，请使用以下命令：

```bash
python -m pytest tests/test_knowledge_base/ -v
```

要运行特定的测试文件：

```bash
python -m pytest tests/test_knowledge_base/test_document_stats.py -v
python -m pytest tests/test_knowledge_base/test_frontend_integration.py -v
```