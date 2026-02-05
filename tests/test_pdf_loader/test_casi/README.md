# CASI端到端集成测试套件

专门用于测试CASI（Chinese Aviation Safety Investigation）参考指南PDF文件处理的端到端集成测试套件。

## 目录结构

```
test_casi/
├── README.md              # 本文件
├── README_CASI_TESTS.md   # 详细技术说明文档
├── e2e_simple_flow.py     # 核心端到端测试文件
└── pdf/                   # 测试PDF文件目录
    └── CASI_RefGuide.pdf  # CASI参考指南PDF文件
```

## 核心测试文件

### e2e_simple_flow.py
这是唯一的测试文件，实现了完整的端到端测试流程：
- PDF文件上传验证
- 文档状态检查  
- 向量搜索功能测试
- 结果验证和报告生成

## 运行测试

```bash
# 使用Django测试运行器（推荐）
python manage.py test tests.test_pdf_loader.test_casi.e2e_simple_flow -v 2

# 或者直接运行测试文件
python tests/test_pdf_loader/test_casi/e2e_simple_flow.py
```

## 测试流程

测试按以下顺序执行：

1. **PDF上传测试**
   - 验证CASi参考指南PDF文件成功上传
   - 检查文档ID和基本信息

2. **文档状态检查**
   - 查询文档处理状态
   - 验证文件大小等元数据

3. **向量搜索测试**
   - 执行多个相关查询：
     - "3 core components in CASi"
     - "CASi architecture overview"
     - "main features of CASi system"
   - 验证搜索结果的相关性

4. **结果验证**
   - 验证数据库记录完整性
   - 检查API端点可用性

## 预期测试结果

测试通过时将显示：
- ✅ PDF文件成功上传（约14MB）
- ✅ 文档状态验证通过
- ✅ 3个搜索查询均返回相关结果
- ✅ 相似度分数在0.81-0.92之间
- ✅ 数据库记录完整性验证
- ✅ 所有API端点正常工作

## 故障排除

如果测试失败，请检查：
1. Django服务是否正常运行
2. 测试PDF文件是否存在且可访问
3. 数据库连接是否正常
4. 相关模型和迁移是否完整

详细技术说明请参考 [README_CASI_TESTS.md](README_CASI_TESTS.md)