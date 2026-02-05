# 测试目录结构说明

## 目录结构

```
tests/
├── __init__.py                    # 测试包初始化文件
├── test_connectivity.py          # API连通性测试
├── test_new_structure.py         # 项目结构完整性测试
├── test_agents/                  # Agents应用测试
│   ├── __init__.py
│   └── test_flows.py
├── test_common/                  # Common应用测试
│   ├── __init__.py
│   └── test_utils.py
├── test_homepage/                # 主页功能测试
│   ├── __init__.py
│   ├── test_homepage.py         # Django客户端主页测试
│   └── test_homepage_access.py  # HTTP请求主页访问测试
├── test_knowledge_base/          # 知识库应用测试
│   ├── __init__.py
│   └── test_mulves.py
└── test_mulvesdb/               # MulvesDB应用测试
    ├── __init__.py
    ├── test_api.py
    └── test_models.py
```

## 测试文件说明

### 根目录测试文件
- **test_connectivity.py**: 测试所有API端点的基本连通性和响应状态
- **test_new_structure.py**: 验证项目文件结构完整性和配置正确性

### 应用级别测试
每个应用都有对应的测试目录，包含该应用特定的功能测试。

### 主页测试 (test_homepage/)
- **test_homepage.py**: 使用Django测试客户端测试主页功能
- **test_homepage_access.py**: 使用HTTP请求测试主页的实际访问情况

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_connectivity.py
python -m pytest tests/test_homepage/

# 运行特定应用的测试
python -m pytest tests/test_agents/
```

---
*最后更新：2026年2月5日*