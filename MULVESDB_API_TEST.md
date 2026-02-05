# MulvesDB 连接测试 API 文档

## 概述

本文档介绍了为 MulvesDB 应用新增的连接测试 API 端点，可以通过 Django REST Framework 直接测试 Milvus 数据库连接。

## 新增的 API 端点

### 1. 健康检查端点（无需认证）

**URL**: `/api/mulvesdb/health/`  
**方法**: `GET`  
**认证**: 不需要  

#### 功能说明
- 快速检查 Milvus 数据库连接状态
- 返回服务健康状况
- 可用于监控和自动化检测

#### 响应示例

**成功响应 (200 OK)**:
```json
{
  "status": "healthy",
  "service": "mulvesdb",
  "connection_host": "localhost",
  "connection_port": 19530,
  "timestamp": "2024-01-01T12:00:00Z",
  "details": "连接测试成功"
}
```

**失败响应 (503 Service Unavailable)**:
```json
{
  "status": "unhealthy",
  "service": "mulvesdb",
  "connection_host": "localhost",
  "connection_port": 19530,
  "timestamp": "2024-01-01T12:00:00Z",
  "details": "连接测试失败: 无法连接到数据库"
}
```

### 2. 连接测试端点（需要认证）

**URL**: `/api/mulvesdb/test-connection/`  
**方法**: `GET`  
**认证**: 需要 JWT Token 或 Session 认证  

#### 功能说明
- 详细的连接测试
- 返回完整的连接配置信息
- 包含测试结果详情

#### 响应示例

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "连接测试成功",
  "connection_info": {
    "host": "localhost",
    "port": 19530,
    "database": "default",
    "ssl_enabled": false,
    "connection_timeout": 30
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "test_details": [
    {
      "test": 1
    }
  ]
}
```

**失败响应 (503 Service Unavailable)**:
```json
{
  "success": false,
  "message": "连接测试失败",
  "connection_info": {
    "host": "localhost",
    "port": 19530,
    "database": "default",
    "ssl_enabled": false,
    "connection_timeout": 30
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "error_details": "无法连接到数据库: Connection refused"
}
```

## 使用方法

### 1. 直接浏览器访问

```
http://localhost:8000/api/mulvesdb/health/
```

### 2. 使用 curl 命令

```bash
# 健康检查（无需认证）
curl http://localhost:8000/api/mulvesdb/health/

# 连接测试（需要认证）
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/mulvesdb/test-connection/
```

### 3. 使用 Python requests

```python
import requests

# 健康检查
response = requests.get('http://localhost:8000/api/mulvesdb/health/')
print(response.json())

# 连接测试（需要认证）
headers = {'Authorization': 'Bearer YOUR_JWT_TOKEN'}
response = requests.get('http://localhost:8000/api/mulvesdb/test-connection/', headers=headers)
print(response.json())
```

### 4. 在前端应用中使用

```javascript
// 健康检查
fetch('/api/mulvesdb/health/')
  .then(response => response.json())
  .then(data => console.log(data));

// 连接测试
fetch('/api/mulvesdb/test-connection/', {
  headers: {
    'Authorization': 'Bearer ' + jwtToken
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## 部署和配置

### 环境变量配置

确保以下环境变量已正确设置：

```bash
# Milvus 连接配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DATABASE=default
MILVUS_USERNAME=
MILVUS_PASSWORD=
MILVUS_TIMEOUT=30
```

### Docker 环境

如果使用 Docker 部署，确保 Milvus 服务正在运行：

```bash
cd apps/mulvesdb/dev_utils
docker-compose up -d
```

## 测试脚本

项目提供了专门的测试脚本来验证这些 API 端点：

```bash
# 运行所有测试
python apps/mulvesdb/test_api_endpoints.py

# 运行单元测试
python apps/mulvesdb/test_api_endpoints.py unit

# 运行HTTP请求测试
python apps/mulvesdb/test_api_endpoints.py http

# 查看使用示例
python apps/mulvesdb/test_api_endpoints.py examples
```

## 错误处理

### 常见错误及解决方案

1. **503 Service Unavailable**
   - Milvus 服务未启动
   - 检查 Docker 容器状态：`docker ps`
   - 确认端口 19530 是否开放

2. **403 Forbidden**
   - 未提供有效的认证信息
   - 确保已登录或提供了正确的 JWT token

3. **500 Internal Server Error**
   - 服务器内部错误
   - 检查 Django 日志获取详细错误信息

## 监控集成

这些 API 端点可以轻松集成到各种监控系统中：

### Prometheus 集成示例

```yaml
scrape_configs:
  - job_name: 'mulvesdb-health'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/mulvesdb/health/'
    scrape_interval: 30s
```

### Kubernetes 健康检查

```yaml
livenessProbe:
  httpGet:
    path: /api/mulvesdb/health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

## 性能考虑

- 健康检查端点设计为轻量级，响应速度快
- 连接测试会实际建立数据库连接，可能需要几百毫秒
- 建议对健康检查端点进行适当的缓存（如果需要）

## 版本历史

- v1.0.0: 初始版本，包含健康检查和连接测试端点
- 支持异步连接测试
- 提供详细的错误信息和调试信息