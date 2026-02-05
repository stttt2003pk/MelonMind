# MulvesDB 测试套件

本目录包含MulvesDB应用的所有测试文件，用于验证Milvus向量数据库的连接和操作功能。

## 测试文件说明

### 核心功能测试
- **test_milvus_final.py** - Milvus写入功能完整测试套件
  - 测试连接、创建集合、插入数据、统计信息、向量搜索等全套功能
  - 独立运行，不依赖Django环境
  - 运行命令：`python test_milvus_final.py`

### 开发工具测试
- **test_local_milvus.py** - 本地开发环境轻量级测试工具
  - 快速验证Milvus连接状态
  - 支持多种测试模式（连接测试、基本操作、环境检查）
  - 运行命令：`python test_local_milvus.py test-connect`

### API测试
- **test_api_endpoints.py** - Django API端点测试
  - 测试健康检查和连接测试API
  - 需要在Django环境中运行
  - 运行命令：`python test_api_endpoints.py`

### Django模型测试
- **test_models.py** - Django模型相关测试
  - 测试MulvesConnection等模型的功能
  - 需要Django测试环境

- **test_api.py** - API功能测试
  - 测试各种API接口的功能
  - 需要完整的Django测试环境

## 运行测试

### 快速测试（推荐日常开发使用）
```bash
# 运行完整功能测试
python test_milvus_final.py

# 快速连接测试
python test_local_milvus.py test-connect

# 环境状态检查
python test_local_milvus.py check-env
```

### Django测试套件
```bash
# 运行所有Django测试
python manage.py test tests.test_mulvesdb

# 运行特定测试文件
python manage.py test tests.test_mulvesdb.test_models
python manage.py test tests.test_mulvesdb.test_api
```

## 环境要求

- Python 3.8+
- pymilvus 2.6.8+
- Milvus数据库服务运行在 localhost:19530
- Docker环境（用于本地Milvus部署）

## 环境变量配置

```bash
export MILVUS_HOST=localhost      # Milvus主机地址
export MILVUS_PORT=19530         # Milvus端口
export MILVUS_DATABASE=default   # 数据库名称
export MILVUS_USERNAME=          # 用户名（可选）
export MILVUS_PASSWORD=          # 密码（可选）
export MILVUS_TIMEOUT=30         # 连接超时时间
```

## 目录结构

```
tests/test_mulvesdb/
├── test_milvus_final.py      # 核心功能测试（独立运行）
├── test_local_milvus.py      # 本地开发工具（独立运行）
├── test_api_endpoints.py     # API端点测试（Django环境）
├── test_models.py           # 模型测试（Django环境）
└── test_api.py              # API功能测试（Django环境）
```

## 测试策略

1. **独立测试优先**：使用test_milvus_final.py和test_local_milvus.py进行快速验证
2. **集成测试补充**：使用Django测试框架进行完整的集成测试
3. **持续集成**：所有测试都应该能在CI/CD环境中自动运行

## 注意事项

- 确保Milvus服务正在运行
- 测试会自动清理创建的测试数据
- 部分测试可能需要网络连接
- 建议在开发环境中定期运行完整测试套件