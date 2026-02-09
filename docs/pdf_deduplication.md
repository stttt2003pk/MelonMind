# PDF文档去重功能说明

## 功能概述

PDF Loader现在支持文档级去重功能，通过计算文件的SHA-256哈希值来识别和避免处理完全相同的PDF文档。

## 技术实现

### 核心组件

1. **文件哈希计算** (`apps/pdfloader/utils.py`)
   - 使用SHA-256算法计算文件二进制内容的哈希值
   - 支持大文件分块读取，避免内存溢出
   - 提供便捷的去重检查函数

2. **数据库模型增强** (`apps/pdfloader/models.py`)
   - 添加 `file_hash` 字段存储文件哈希值
   - 建立哈希值索引优化查询性能
   - 添加类方法用于去重检查

3. **上传流程优化** (`apps/pdfloader/views.py`)
   - 上传时自动计算文件哈希
   - 检查是否已存在相同哈希的文档
   - 发现重复时返回现有文档而非重新处理

### 数据库变更

新增迁移文件：
- `0002_add_file_hash_field.py`: 添加file_hash字段和索引
- `0003_make_file_hash_unique.py`: 设置file_hash字段为唯一约束

## 使用方式

### API调用示例

```python
import requests

# 上传PDF文件
files = {'file': open('document.pdf', 'rb')}
data = {
    'title': '我的PDF文档',
    'milvus_connection_id': 1,
    'collection_name': 'my_documents'
}

response = requests.post(
    'http://localhost:8000/api/pdfloader/upload/',
    files=files,
    data=data
)

# 检查是否为重复文档
result = response.json()
if result.get('duplicate'):
    print(f"检测到重复文档，ID: {result['existing_document_id']}")
else:
    print(f"新文档上传成功，ID: {result['data']['id']}")
```

### 响应格式

**新文档上传成功：**
```json
{
    "success": true,
    "message": "PDF文件上传成功，正在后台处理",
    "data": {
        "id": 123,
        "title": "文档标题",
        "file_hash": "a1b2c3d4e5f6...",
        // ... 其他字段
    },
    "duplicate": false
}
```

**重复文档检测：**
```json
{
    "success": true,
    "message": "检测到重复文档，返回已有记录",
    "data": {
        "id": 456,
        "title": "已存在的文档",
        "file_hash": "a1b2c3d4e5f6...",
        // ... 其他字段
    },
    "duplicate": true,
    "existing_document_id": 456
}
```

## 性能优势

1. **存储优化**: 避免重复存储相同内容的文档
2. **处理效率**: 跳过已处理文档，节省计算资源
3. **用户体验**: 快速响应重复上传请求
4. **数据一致性**: 确保同一文档只有一个权威版本

## 注意事项

1. **哈希算法**: 使用SHA-256，具有极低的碰撞概率
2. **文件完整性**: 基于完整文件二进制内容计算哈希
3. **向后兼容**: 不影响现有功能的正常使用
4. **错误处理**: 哈希计算失败时仍允许正常上传

## 测试验证

运行测试脚本验证功能：
```bash
python test_deduplication_simple.py
```

该脚本会测试：
- 文件哈希计算准确性
- 模型方法功能
- 重复文档检测逻辑