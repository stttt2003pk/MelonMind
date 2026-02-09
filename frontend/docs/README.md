# 前端开发文档

## 项目概述

MelonMind 前端项目基于 Vue 3 + Vite 构建，采用现代化的前端技术栈。

## 项目结构

```
frontend/
├── melonmind/                 # 主要前端应用
│   ├── src/
│   │   ├── assets/           # 静态资源
│   │   ├── components/       # 可复用组件
│   │   ├── router/          # 路由配置
│   │   ├── services/        # API服务层
│   │   ├── stores/          # 状态管理
│   │   ├── views/           # 页面视图
│   │   ├── App.vue          # 根组件
│   │   └── main.ts          # 入口文件
│   ├── package.json         # 依赖配置
│   └── vite.config.ts       # 构建配置
└── docs/                    # 前端文档（本文档所在目录）
```

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **语言**: TypeScript
- **HTTP客户端**: Axios
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI框架**: Bootstrap + 自定义组件

## 核心组件

### 1. PDFLoaderView.vue
**主要功能**:
- PDF文件拖拽上传
- 批量文件处理
- 实时进度跟踪
- 文件预览功能
- 处理状态显示

**核心特性**:
- 支持多文件同时上传
- 文件类型和大小验证
- 处理进度可视化
- 错误处理和用户反馈

### 2. NotificationManager.vue
**功能**: 全局通知系统
- 成功/错误/警告/信息提示
- 自动消失和手动关闭
- 进度条显示
- 响应式设计

### 3. LoadingOverlay.vue
**功能**: 全局加载遮罩
- 处理状态显示
- 进度跟踪
- 步骤指示器
- 文件处理进度

### 4. FilePreview.vue
**功能**: 文件预览组件
- PDF文件预览
- 图片预览和缩放
- 文本文件查看
- 下载和打印功能

## API服务层

### api.js
**主要功能**:
- 统一的HTTP请求封装
- 请求/响应拦截器
- 错误处理和用户友好提示
- 文件上传专用配置
- 批量处理支持

**核心方法**:
```javascript
// PDF处理相关
pdfLoaderAPI.uploadPDF()
pdfLoaderAPI.batchUploadPDF()
pdfLoaderAPI.getDocuments()
pdfLoaderAPI.getDocumentDetail()

// 知识库相关
knowledgeBaseAPI.getDocumentStats()
knowledgeBaseAPI.getSystemHealth()
```

## 路由配置

```javascript
// router/index.ts
const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/pdfloader',
    name: 'pdfloader',
    component: PDFLoaderView
  }
]
```

## 开发环境配置

### Vite配置 (vite.config.ts)
```typescript
export default defineConfig({
  plugins: [
    vue(),
    vueJsx()
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

## 测试策略

### 1. 手动测试
**本地开发测试流程**:
```bash
# 1. 启动前端开发服务器
cd frontend/melonmind
npm run dev

# 2. 启动后端服务
cd ../..
python manage.py runserver

# 3. 访问应用
# 前端: http://localhost:5174/
# 后端API: http://localhost:8000/api/
```

**测试要点**:
- 文件上传功能
- 拖拽交互
- 进度显示
- 错误处理
- 响应式布局

### 2. 组件测试
**单元测试工具**: Vitest
```bash
npm run test:unit
```

### 3. 端到端测试
**工具**: Playwright
```bash
npm run test:e2e
```

## 部署配置

### 生产环境构建
```bash
npm run build
```

### 环境变量配置
```bash
# .env.production
VITE_API_BASE_URL=/api
```

## 性能优化

1. **代码分割**: 路由级别代码分割
2. **懒加载**: 组件按需加载
3. **缓存策略**: HTTP缓存头配置
4. **打包优化**: Vite生产构建优化

## 常见问题

### 1. 跨域问题
通过Vite代理配置解决开发环境跨域

### 2. 文件上传大文件支持
配置适当的超时时间和分片上传

### 3. 浏览器兼容性
使用现代浏览器API，必要时添加polyfill

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 版本历史

- v1.0.0: 初始版本，基础PDF上传功能
- v1.1.0: 添加文件预览和批量处理功能