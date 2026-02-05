# CASI端到端集成测试套件

专门用于测试CASI（Chinese Aviation Safety Investigation）参考指南PDF文件处理的端到端集成测试套件。

## 目录结构

```
test_casi/
├── README.md                           # 本文件
├── E2E_TEST_SUMMARY.md                # 端到端测试总结
├── README_CASI_TESTS.md               # 详细测试说明文档
├── run_casi_tests.py                  # 统一测试运行器
├── simple_casi_test.py                # 简单的CASI测试
├── basic_e2e_test.py                  # 基础端到端测试
├── complete_pipeline_validation.py    # 完整流水线验证
├── core_functionality_demo.py         # 核心功能演示
├── final_validation_test.py           # 最终验证测试
├── test_casi_api_flow.py              # CASI API流程测试
├── test_casi_guide_integration.py     # CASI指南集成测试
├── test_casi_real_embedding.py        # CASI真实嵌入测试
├── test_real_embedding_standalone.py  # 独立的真实嵌入测试
├── direct_processing_test.py          # 直接处理测试
└── simple_upload_test.py              # 简单上传测试
```

## 测试文件说明

### 基础验证测试
- **simple_casi_test.py**: 简单的独立测试，验证基本功能
- **validate_casi_environment.py**: 环境配置检查
- **test_qwen_api.py**: Qwen API密钥有效性验证

### 核心功能测试
- **test_casi_api_flow.py**: 测试完整的API调用流程
- **test_casi_guide_integration.py**: 全面的集成测试
- **test_casi_real_embedding.py**: 使用真实Embedding服务的测试

### 独立测试
- **test_real_embedding_standalone.py**: 不依赖Django的纯Python测试

### 工具脚本
- **run_casi_tests.py**: 统一的测试运行入口

## 运行测试

### 快速环境验证
```bash
poetry run python tests/test_pdf_loader/test_casi/simple_casi_test.py
```

### 完整测试套件
```bash
poetry run python tests/test_pdf_loader/test_casi/run_casi_tests.py
```

### 真实环境测试
```bash
poetry run python tests/test_pdf_loader/test_casi/run_casi_tests.py --real --use-real-embedding
```

### 特定测试
```bash
# 只运行API流程测试
poetry run python tests/test_pdf_loader/test_casi/run_casi_tests.py --api-only

# 只运行集成测试
poetry run python tests/test_pdf_loader/test_casi/run_casi_tests.py --integration

# 只运行真实Embedding测试
poetry run python tests/test_pdf_loader/test_casi/run_casi_tests.py --embedding-only
```

## 测试覆盖范围

### 功能测试
- ✅ PDF文件上传验证
- ✅ 文本提取和分块处理
- ✅ 向量化处理（Mock和真实服务）
- ✅ Milvus向量存储
- ✅ 向量搜索功能
- ✅ 使用查询："3 core components in CASI"

### 环境测试
- ✅ 依赖项检查
- ✅ API密钥验证
- ✅ 服务连通性测试
- ✅ 性能基准测试

## 预期测试结果

当所有测试通过时，您应该看到：
- PDF文件成功处理
- 生成相关的文本分块
- 向量存储到Milvus数据库
- 搜索"CASI的3个核心组件"返回相关结果
- 相似度分数反映内容相关性

## 故障排除

如果测试失败，请检查：
1. 数据库服务是否运行
2. Milvus服务是否可用
3. API密钥是否正确配置
4. 网络连接是否正常
5. 依赖包是否完整安装

详细故障排除指南请参考 [README_CASI_TESTS.md](README_CASI_TESTS.md)