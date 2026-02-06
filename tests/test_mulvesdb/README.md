# Milvus 数据库测试

## 核心测试文件

### `test_milvus_final.py` (唯一测试文件)
- **用途**: Milvus 写入功能的最终验证测试
- **特点**: 使用 pymilvus 2.6.8 的正确 API
- **测试内容**: 
  - 连接测试
  - 集合创建
  - 数据插入
  - 向量搜索
  - 统计信息获取
- **运行方式**: `python test_milvus_final.py`

## 快速开始

### 环境准备
```bash
# 启动 Milvus 服务
docker-compose -f apps/mulvesdb/dev_utils/docker-compose.yml up -d

# 安装依赖
pip install pymilvus==2.6.8
```

### 运行测试
```bash
# 执行核心测试
python test_milvus_final.py

# 查看使用示例
python test_milvus_final.py examples
```

## 测试验证
运行测试后会显示详细的执行过程和结果，确保所有功能正常工作。