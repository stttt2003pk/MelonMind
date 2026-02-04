# MelonMind - 网络运维智能助手

基于 Django 的后台管理系统，集成 LangChain/LangGraph 智能代理和 Mulves 知识库，专为网络工程师设计的运维助手平台。

## 功能特性

### 🤖 智能代理 (Agents)
- 基于 LangChain/LangGraph 的智能流程编排
- 网络设备自动化操作
- 配置备份与恢复
- 健康状态监控
- 故障自动诊断

### 📚 知识库管理
- 集成 Mulves 知识库系统
- 智能搜索与推荐
- 网络运维最佳实践
- 故障排除指南
- 配置模板库

### 🔧 核心功能
- RESTful API 接口
- 异步任务处理 (Celery)
- 权限管理与认证
- 操作日志记录
- 数据统计分析

## 技术栈

- **后端框架**: Django 4.2
- **API 框架**: Django REST Framework
- **AI 框架**: LangChain, LangGraph
- **知识库**: Mulves
- **异步处理**: Celery + Redis
- **数据库**: PostgreSQL
- **依赖管理**: Poetry

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd MelonMind

# 安装 Poetry (如果未安装)
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 2. 配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 数据库初始化

```bash
# 创建数据库
createdb melonmind

# 运行迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 初始化知识库
python scripts/setup_knowledge_base.py
```

### 4. 启动服务

```bash
# 启动 Django 开发服务器
python manage.py runserver

# 启动 Celery worker (新终端)
celery -A config worker --loglevel=info

# 启动 Celery beat (新终端，如果需要定时任务)
celery -A config beat --loglevel=info
```

## 项目结构

```
MelonMind/
├── config/                 # Django 配置
├── apps/                   # 应用模块
│   ├── agents/            # 智能代理应用
│   ├── knowledge_base/    # 知识库应用
│   └── common/            # 通用工具
├── tests/                 # 测试文件
├── scripts/               # 脚本文件
├── logs/                  # 日志文件
└── manage.py             # Django 管理脚本
```

## API 接口

### Agent 流程管理
- `POST /api/agents/flows/` - 创建流程
- `GET /api/agents/flows/` - 获取流程列表
- `POST /api/agents/flows/{id}/execute/` - 执行流程

### 知识库查询
- `POST /api/knowledge/query/search/` - 搜索知识
- `GET /api/knowledge/entries/` - 获取知识条目
- `POST /api/knowledge/entries/` - 创建知识条目

## 开发指南

### 代码规范
- 遵循 PEP 8 Python 编码规范
- 使用类型提示
- 编写单元测试

### 测试运行
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_agents/

# 生成测试覆盖率报告
pytest --cov=apps
```

## 部署说明

### 生产环境配置
1. 设置 `DEBUG=False`
2. 配置生产数据库
3. 设置合适的 SECRET_KEY
4. 配置 HTTPS
5. 设置适当的权限和防火墙规则

### Docker 部署 (可选)
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请联系项目维护者。