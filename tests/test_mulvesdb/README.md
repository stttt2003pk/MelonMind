# Milvus 数据库测试

## 核心测试文件

### `test_milvus_final.py`
- **用途**: Milvus 写入功能的最终验证测试
- **特点**: 使用 pymilvus 2.6.8 的正确 API
- **测试内容**: 
  - 连接测试
  - 集合创建
  - 数据插入
  - 向量搜索
  - 统计信息获取
- **运行方式**: `python test_milvus_final.py`

### `test_chunk_deduplication.py`
- **用途**: 块级去重功能单元测试
- **特点**: Django TestCase 测试框架
- **测试内容**:
  - 哈希计算功能
  - 去重管理器
  - 块数据过滤
  - 数据库模型操作
- **运行方式**: `python manage.py test tests.test_mulvesdb.test_chunk_deduplication`

### `test_chunk_dedup_manual.py`
- **用途**: 块级去重功能手动验证测试
- **特点**: 独立Python脚本，无需Django环境
- **测试内容**:
  - 核心功能验证
  - 真实场景演示
  - 去重效益展示
- **运行方式**: `python test_chunk_dedup_manual.py`

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

## 相关文档

### `FINAL_TEST_REPORT.md`
- **内容**: 向量元数据追踪功能完整测试报告
- **涵盖**: 测试结果汇总、功能验证、Bug修复记录

### `METADATA_TESTING_SUMMARY.md`  
- **内容**: 元数据追踪功能测试总结
- **涵盖**: 功能特性确认、使用验证示例

### `BLOCK_DEDUPLICATION_IMPLEMENTATION_SUMMARY.md`
- **内容**: 块级去重功能完整实施总结
- **涵盖**: 技术架构、实现细节、集成情况、使用说明

### `BLOCK_DEDUPLICATION_TODO.md`  
- **内容**: 块级去重功能待完善事项
- **涵盖**: 未来优化方向、功能扩展计划

## 测试验证
运行测试后会显示详细的执行过程和结果，确保所有功能正常工作。

### 最新测试状态
- ✅ **向量元数据追踪**: 核心功能和集成测试全部通过
- ✅ **Milvus基础功能**: 写入、查询、统计等功能正常
- ✅ **块级去重功能**: 哈希计算、去重管理等功能完备