# PDF Loader 使用指南

## 概述

PDF Loader是一个Django应用，用于处理PDF文件并将其转换为向量存储到Milvus数据库中。该应用集成了Qwen模型进行文本embedding，提供了完整的PDF处理流水线。

## 功能特性

- 📄 PDF文件读取和文本提取
- 🔪 智能文本分块（chunking）
- 🤖 Qwen模型文本embedding
- 📊 向量存储到Milvus数据库
- 🔄 异步处理支持
- 🔍 向量相似度搜索
- 📈 处理状态跟踪

## 安装和配置

### 1. 依赖安装

```bash
pip install PyPDF2 langchain openai pymilvus
```

### 2. Django设置

在 `settings.py` 中添加应用：

```python
INSTALLED_APPS = [
    # ... 其他应用
    'apps.pdfloader',
]

# Qwen API配置
QWEN_API_KEY = 'your_qwen_api_key_here'
QWEN_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
```

### 3. 数据库迁移

```bash
python manage.py makemigrations pdfloader
python manage.py migrate
```

### 4. URL配置

在主 `urls.py` 中添加：

```python
from django.urls import path, include

urlpatterns = [
    # ... 其他URL
    path('api/pdfloader/', include('apps.pdfloader.urls')),
]
```

## 核心组件

### 1. PDF处理器 (`pdf_processor.py`)

负责PDF文件的读取和智能分块：

```python
from apps.pdfloader.pdf_processor import PDFProcessor

processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
chunks = list(processor.process_pdf('/path/to/document.pdf'))

for chunk in chunks:
    print(f"分块 {chunk.chunk_index}: {chunk.content[:50]}...")
```

### 2. Embedding服务 (`embedding.py`)

提供Qwen模型的文本embedding功能：

```python
from apps.pdfloader.embedding import get_embedding_service

# 获取embedding服务
embedding_service = get_embedding_service()

# 单个文本embedding
result = embedding_service.embed_text("要嵌入的文本")

# 批量embedding
texts = ["文本1", "文本2", "文本3"]
results = embedding_service.embed_batch(texts)
```

### 3. 向量存储服务 (`storage.py`)

处理与Milvus数据库的交互：

```python
from apps.pdfloader.storage import PDFVectorStorageService

async def store_pdf_vectors():
    async with PDFVectorStorageService(milvus_connection_id=1) as storage:
        # 创建集合
        await storage.create_document_collection('my_pdf_collection')
        
        # 存储分块数据
        chunks_data = [
            {'content': '分块内容1', 'page_number': 1, 'chunk_index': 0},
            {'content': '分块内容2', 'page_number': 1, 'chunk_index': 1}
        ]
        
        result = await storage.store_pdf_chunks(
            document_id=1,
            chunks_data=chunks_data,
            collection_name='my_pdf_collection'
        )
```

## API接口

### 1. 上传PDF文件

```http
POST /api/pdfloader/upload/
Content-Type: multipart/form-data

Form Data:
- title: 文档标题
- file: PDF文件
- milvus_connection_id: Milvus连接ID
- collection_name: 集合名称
```

### 2. 获取文档列表

```http
GET /api/pdfloader/documents/
```

### 3. 获取文档详情

```http
GET /api/pdfloader/documents/{id}/
```

### 4. 获取文档分块

```http
GET /api/pdfloader/documents/{id}/chunks/
```

### 5. 查询处理状态

```http
GET /api/pdfloader/documents/{id}/status/
```

### 6. 向量搜索

```http
POST /api/pdfloader/search/
Content-Type: application/json

{
    "query_text": "搜索查询文本",
    "collection_name": "集合名称",
    "limit": 10
}
```

## 使用示例

### 1. 基本使用流程

```python
import requests

# 1. 上传PDF文件
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

document_id = response.json()['data']['id']
print(f"文档ID: {document_id}")

# 2. 查询处理状态
status_response = requests.get(
    f'http://localhost:8000/api/pdfloader/documents/{document_id}/status/'
)
print(f"处理状态: {status_response.json()['data']['status']}")

# 3. 执行向量搜索
search_data = {
    'query_text': '查找相关内容',
    'collection_name': 'my_documents',
    'limit': 5
}

search_response = requests.post(
    'http://localhost:8000/api/pdfloader/search/',
    json=search_data
)

results = search_response.json()['data']
for result in results:
    print(f"相似内容: {result['content']}")
```

### 2. Python SDK使用

```python
from apps.pdfloader.pdf_processor import PDFProcessor
from apps.pdfloader.embedding import get_embedding_service
from apps.pdfloader.storage import PDFProcessingPipeline

# 处理PDF文件
processor = PDFProcessor()
chunks = list(processor.process_pdf('document.pdf'))

# 生成embedding
embedding_service = get_embedding_service()
embeddings = embedding_service.embed_batch([chunk.content for chunk in chunks])

# 存储到Milvus
pipeline = PDFProcessingPipeline(milvus_connection_id=1)
# 异步处理
import asyncio
asyncio.run(pipeline.process_pdf_document(document, 'document.pdf'))
```

## 配置选项

### PDF处理器配置

```python
PDFProcessor(
    chunk_size=1000,      # 分块大小
    chunk_overlap=200     # 分块重叠
)
```

### Embedding服务配置

```python
# 生产环境使用真实Qwen API
QWEN_API_KEY = 'your_actual_api_key'

# 测试环境使用mock服务
USE_MOCK_EMBEDDING = True
```

### Milvus连接配置

通过Django admin界面或API创建Milvus连接配置：

- 主机地址
- 端口号  
- 用户名/密码
- 数据库名称

## 错误处理

常见错误和解决方案：

### 1. PDF文件处理失败
```python
# 检查文件格式和权限
try:
    chunks = list(processor.process_pdf(file_path))
except Exception as e:
    print(f"PDF处理失败: {e}")
```

### 2. Embedding生成失败
```python
# 使用mock服务进行测试
embedding_service = get_embedding_service(use_mock=True)
```

### 3. Milvus连接失败
```python
# 检查连接配置
try:
    async with PDFVectorStorageService(connection_id) as storage:
        # 处理逻辑
except ConnectionError as e:
    print(f"Milvus连接失败: {e}")
```

## 性能优化建议

1. **批量处理**: 使用批量embedding减少API调用次数
2. **异步处理**: 利用异步特性提高处理效率
3. **合理的分块大小**: 根据内容特点调整chunk_size参数
4. **缓存策略**: 对频繁查询的结果进行缓存
5. **监控和日志**: 启用详细的日志记录便于调试

## 监控指标

可以通过以下方式监控系统性能：

- 处理文档数量和成功率
- 平均处理时间
- Embedding生成耗时
- Milvus存储性能
- API响应时间

## 故障排除

### 日志查看
```bash
# 查看Django日志
tail -f logs/django.log

# 查看应用特定日志
tail -f logs/pdfloader.log
```

### 常见问题诊断
1. 检查Milvus服务状态
2. 验证Qwen API密钥有效性
3. 确认PDF文件格式正确
4. 检查磁盘空间和内存使用

## 版本历史

- v1.0.0: 初始版本，支持基本PDF处理和向量存储
- v1.1.0: 添加异步处理支持和性能优化