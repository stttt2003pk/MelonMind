# MelonMind API 连通性测试指南

## 🚀 快速开始

### 1. 启动开发服务器

```bash
# 在项目根目录下运行
python manage.py runserver
```

服务器将在 `http://127.0.0.1:8000` 启动

### 2. 测试连通性

#### 方法一：使用浏览器访问
直接在浏览器中打开以下URL：
- 主页: http://127.0.0.1:8000/api/
- 健康检查: http://127.0.0.1:8000/api/health/
- 管理后台: http://127.0.0.1:8000/admin/

#### 方法二：使用curl命令
```bash
# 测试主页
curl http://127.0.0.1:8000/api/

# 测试健康检查
curl http://127.0.0.1:8000/api/health/

# 测试其他端点
curl http://127.0.0.1:8000/api/agents/
curl http://127.0.0.1:8000/api/knowledge/
```

#### 方法三：使用Python测试脚本
```bash
# 运行自动化测试脚本
python test_connectivity.py
```

## 🔧 可用的API端点

| 端点 | 描述 | 方法 |
|------|------|------|
| `/api/` | 默认主页，显示API信息 | GET |
| `/api/health/` | 健康检查端点 | GET |
| `/api/agents/` | Agents相关API | GET/POST等 |
| `/api/knowledge/` | 知识库相关API | GET/POST等 |
| `/admin/` | Django管理后台 | GET |

## 📋 预期响应示例

### 主页响应 (`/api/`)
```json
{
  "message": "Welcome to MelonMind API",
  "status": "success",
  "version": "1.0.0",
  "endpoints": {
    "agents": "/api/agents/",
    "knowledge_base": "/api/knowledge/",
    "admin": "/admin/"
  }
}
```

### 健康检查响应 (`/api/health/`)
```json
{
  "status": "healthy",
  "service": "MelonMind API"
}
```

## ⚠️ 常见问题排查

### 1. 连接被拒绝
- 确认Django服务器正在运行
- 检查端口8000是否被占用
- 确认防火墙设置

### 2. 404错误
- 确认URL路径正确
- 检查urls.py配置
- 确认应用已正确注册

### 3. 导入错误
- 确认所有依赖已安装：`pip install -r requirements.txt`
- 检查Python环境
- 确认项目结构正确

## 🛠️ 开发环境设置

### 安装依赖
```bash
pip install -r requirements.txt
# 或者如果使用poetry
poetry install
```

### 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 创建超级用户（可选）
```bash
python manage.py createsuperuser
```

## 📊 监控和日志

查看服务器日志：
```bash
# 在运行服务器的终端中查看实时日志
tail -f logs/app.log
```

## 🔒 安全提醒

- 开发环境中启用了DEBUG模式
- 生产环境请务必关闭DEBUG并配置适当的安全设置
- 不要在生产环境中暴露管理后台