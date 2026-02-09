# MulvesDB App 使用指南

## 简介

MulvesDB是一个专门用于连接和操作Mulves数据库的Django应用，提供了完整的数据库连接管理、查询执行、缓存机制和监控功能。

## 功能特性

### 1. 数据库连接管理
- 支持多种数据库连接配置
- 连接参数验证和测试
- SSL连接支持
- 连接池管理

### 2. 查询执行
- 异步查询执行
- SQL注入防护
- 查询性能监控
- 结果缓存机制

### 3. 缓存管理
- 智能缓存策略
- 缓存过期管理
- 缓存清理功能

### 4. 监控和日志
- 完整的查询日志记录
- 性能指标收集
- 错误追踪

## API接口说明

### 基础URL
```
/api/mulves/
```

### 主要端点

#### 连接管理
- `GET /api/mulves/connections/` - 获取连接列表
- `POST /api/mulves/connections/` - 创建新连接
- `GET /api/mulves/connections/{id}/` - 获取连接详情
- `PUT /api/mulves/connections/{id}/` - 更新连接
- `DELETE /api/mulves/connections/{id}/` - 删除连接
- `POST /api/mulves/connections/test-connection/` - 测试连接

#### 查询执行
- `POST /api/mulves/queries/` - 执行数据库查询

#### 日志查询
- `GET /api/mulves/query-logs/` - 获取查询日志
- `GET /api/mulves/query-logs/?connection_id={id}` - 按连接过滤日志

#### 缓存管理
- `GET /api/mulves/data-cache/` - 获取缓存列表
- `POST /api/mulves/data-cache/` - 创建缓存
- `DELETE /api/mulves/data-cache/clear-cache/` - 清除缓存

## 使用示例

### 1. 创建数据库连接

```bash
curl -X POST http://localhost:8000/api/mulves/connections/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_token_here" \
  -d '{
    "name": "Production DB",
    "host": "db.example.com",
    "port": 5432,
    "database": "production_db",
    "username": "db_user",
    "password": "db_password",
    "ssl_enabled": true,
    "connection_timeout": 30
  }'
```

### 2. 测试连接

```bash
curl -X POST http://localhost:8000/api/mulves/connections/test-connection/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_token_here" \
  -d '{
    "host": "db.example.com",
    "port": 5432,
    "database": "test_db",
    "username": "test_user",
    "password": "test_password",
    "ssl_enabled": false
  }'
```

### 3. 执行查询

```bash
curl -X POST http://localhost:8000/api/mulves/queries/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_token_here" \
  -d '{
    "connection_id": 1,
    "query_sql": "SELECT * FROM users WHERE active = true LIMIT 100",
    "use_cache": true,
    "cache_timeout": 300
  }'
```

### 4. 查看查询日志

```bash
curl -X GET "http://localhost:8000/api/mulves/query-logs/?connection_id=1" \
  -H "Authorization: Token your_token_here"
```

## 模型结构

### MulvesConnection (连接配置)
```python
class MulvesConnection(models.Model):
    name = models.CharField(max_length=100)          # 连接名称
    host = models.CharField(max_length=255)          # 主机地址
    port = models.IntegerField()                     # 端口号
    database = models.CharField(max_length=100)      # 数据库名
    username = models.CharField(max_length=100)      # 用户名
    password = models.CharField(max_length=255)      # 密码
    ssl_enabled = models.BooleanField(default=False) # SSL启用
    connection_timeout = models.IntegerField()       # 连接超时
    is_active = models.BooleanField(default=True)    # 是否激活
```

### MulvesQueryLog (查询日志)
```python
class MulvesQueryLog(models.Model):
    connection = models.ForeignKey(MulvesConnection)
    query_sql = models.TextField()                   # SQL语句
    execution_time = models.FloatField()             # 执行时间(ms)
    result_count = models.IntegerField()             # 结果数量
    error_message = models.TextField()               # 错误信息
    created_at = models.DateTimeField()              # 执行时间
```

### MulvesDataCache (数据缓存)
```python
class MulvesDataCache(models.Model):
    cache_key = models.CharField(max_length=255)     # 缓存键
    data = models.JSONField()                        # 缓存数据
    expires_at = models.DateTimeField()              # 过期时间
```

## 本地测试环境配置

### 使用Docker Compose部署Milvus
项目提供了预配置的Docker Compose文件用于本地测试：

```bash
# 进入开发工具目录
cd apps/mulvesdb/dev_utils

# 启动Milvus服务
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### 环境变量配置
```bash
# 复制环境变量模板
cp .env.local.example .env.local

# 编辑配置文件
vim .env.local
```

### 本地测试
```bash
# 测试连接
cd ../..
python apps/mulvesdb/test_local_milvus.py test-connect

# 测试基本操作
python apps/mulvesdb/test_local_milvus.py test-ops

# 检查环境状态
python apps/mulvesdb/test_local_milvus.py check-env
```

### 生产环境配置
```bash
# 在主.env文件中添加以下配置
MULVES_DB_HOST=your_database_host
MULVES_DB_PORT=5432
MULVES_DB_NAME=your_database_name
MULVES_DB_USER=your_username
MULVES_DB_PASSWORD=your_password
```

### 依赖包
确保安装了以下Python包：
```toml
asyncpg = "^0.27.0"  # PostgreSQL异步驱动
```

## 安全注意事项

1. **密码安全**：数据库密码存储应考虑加密
2. **SQL注入防护**：使用参数化查询
3. **访问控制**：确保只有授权用户可以访问API
4. **连接池管理**：合理配置连接池大小
5. **日志敏感信息**：避免在日志中记录敏感数据

## 性能优化建议

1. **连接复用**：使用连接池减少连接开销
2. **查询缓存**：对频繁查询启用缓存
3. **索引优化**：在数据库层面优化查询性能
4. **批量操作**：合并多个小查询为批量操作
5. **异步处理**：长时间运行的查询使用异步执行

## 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连通性
   - 验证数据库凭据
   - 确认防火墙设置

2. **查询超时**
   - 增加连接超时时间
   - 优化SQL查询
   - 检查数据库负载

3. **缓存问题**
   - 检查缓存键冲突
   - 验证过期时间设置
   - 清理过期缓存

### 监控指标

- 连接成功率
- 平均查询响应时间
- 缓存命中率
- 错误率统计