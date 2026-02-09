# PDF Loader 前端组件文档

## 概述

PDF Loader 是 MelonMind 系统的核心功能模块，提供完整的PDF文档上传、处理和管理功能。

## 组件架构

### 主要组件关系图

```
PDFLoaderView.vue (主容器)
├── NotificationManager.vue (通知系统)
├── LoadingOverlay.vue (加载遮罩)
├── FilePreview.vue (文件预览)
└── 各种子组件...
```

## 核心功能详解

### 1. 文件上传功能

#### 拖拽上传
```vue
<div 
  class="upload-area" 
  @dragover.prevent="handleDragOver"
  @drop.prevent="handleDrop"
  @click="triggerFileSelect"
>
```

**特性**:
- 支持文件拖拽放置
- 视觉反馈（悬停、拖拽状态）
- 多文件同时选择
- 文件类型过滤

#### 文件验证
```javascript
const validateFile = (file) => {
  // 文件类型检查
  const validTypes = ['application/pdf']
  // 文件大小限制 (50MB)
  const maxSize = 50 * 1024 * 1024
  // 重复文件检测
}
```

### 2. 批量处理系统

#### 处理队列管理
```javascript
const processFiles = async () => {
  const filesToProcess = fileList.value.filter(f => f.status === 'pending')
  const results = await pdfLoaderAPI.batchUploadPDF(
    filesToProcess.map(f => f.file),
    options,
    progressCallback
  )
}
```

#### 进度跟踪
- 整体进度显示
- 单文件进度条
- 实时状态更新
- 失败文件重试机制

### 3. 用户反馈系统

#### 通知管理
```javascript
import { notify } from '@/components/NotificationManager.vue'

// 成功通知
notify.success('文件上传成功', '操作完成')

// 错误通知
notify.error('上传失败', '错误信息')

// 警告通知
notify.warning('文件过大', '提醒信息')
```

#### 加载状态
```vue
<LoadingOverlay 
  :is-loading="processing"
  :title="loadingTitle"
  :message="loadingMessage"
  :progress="overallProgress"
/>
```

### 4. 文件预览功能

#### PDF预览组件
```vue
<FilePreview 
  :show-preview="showPreview"
  :file-url="previewFileUrl"
  :file-name="previewFileName"
  :file-type="previewFileType"
/>
```

**支持功能**:
- PDF页面浏览
- 缩放控制
- 下载功能
- 打印支持

## 使用的第三方工具

### 1. 开发工具
- **Vite**: 构建工具和开发服务器
- **Vue DevTools**: Vue应用调试工具
- **TypeScript**: 类型检查和开发支持

### 2. UI组件库
- **Bootstrap**: 基础UI框架
- **Font Awesome**: 图标库
- **自定义组件**: NotificationManager, LoadingOverlay等

### 3. HTTP客户端
- **Axios**: HTTP请求处理
- **自定义拦截器**: 请求/响应处理

### 4. 状态管理
- **Pinia**: Vue状态管理
- **Composition API**: Vue 3响应式系统

## 测试方法

### 1. 手动功能测试

#### 基础功能测试
```bash
# 启动开发环境
cd frontend/melonmind
npm run dev  # 前端运行在 localhost:5174

# 后端服务
python manage.py runserver  # 后端运行在 localhost:8000
```

**测试步骤**:
1. 访问 `http://localhost:5174/pdfloader`
2. 测试文件拖拽上传
3. 验证文件类型限制
4. 检查进度显示
5. 测试文件预览功能

#### 测试用例清单
- [ ] 单个PDF文件上传
- [ ] 多个PDF文件批量上传
- [ ] 非PDF文件拒绝上传
- [ ] 超大文件(>50MB)限制测试
- [ ] 重复文件检测
- [ ] 上传过程中取消操作
- [ ] 网络中断恢复
- [ ] 文件预览功能
- [ ] 通知系统显示
- [ ] 响应式布局适配

### 2. 自动化测试

#### 单元测试
```bash
npm run test:unit
```

#### 端到端测试
```bash
npm run test:e2e
```

### 3. 性能测试

#### 关键性能指标
- 文件上传速度
- 页面加载时间
- 内存使用情况
- 响应时间

## API集成

### 后端接口调用

#### 上传接口
```javascript
const uploadResult = await pdfLoaderAPI.uploadPDF(formData, progressCallback)
```

#### 批量处理接口
```javascript
const batchResults = await pdfLoaderAPI.batchUploadPDF(
  files, 
  {
    milvusConnectionId: 1,
    collectionName: 'pdf_docs_' + Date.now(),
    enableDeduplication: true
  },
  progressCallback
)
```

### 错误处理机制

```javascript
try {
  const result = await apiCall()
  // 处理成功响应
} catch (error) {
  // 统一错误处理
  const userMessage = error.userMessage || '操作失败'
  notify.error(userMessage)
}
```

## 配置选项

### 环境配置
```bash
# 开发环境
VITE_API_BASE_URL=http://localhost:8000/api

# 生产环境
VITE_API_BASE_URL=/api
```

### 功能开关
```javascript
const deduplicateEnabled = ref(true)  // 去重功能
const collectionName = ref('')        // 集合名称
const maxFileSize = 50 * 1024 * 1024  // 最大文件大小(字节)
```

## 最佳实践

### 1. 用户体验优化
- 提供清晰的操作指引
- 实时反馈处理状态
- 合理的错误提示信息
- 流畅的动画过渡效果

### 2. 性能优化
- 文件分片上传（大文件）
- 请求并发控制
- 组件懒加载
- 图片压缩处理

### 3. 代码维护
- 组件职责单一
- 状态管理清晰
- API调用统一
- 错误处理完整

## 故障排除

### 常见问题及解决方案

1. **上传失败**
   - 检查网络连接
   - 验证文件格式和大小
   - 查看后端服务状态

2. **预览功能异常**
   - 确认文件URL有效性
   - 检查浏览器兼容性
   - 验证文件完整性

3. **进度显示不准确**
   - 检查上传回调函数
   - 验证计算逻辑
   - 确认网络稳定性

## 未来扩展计划

- [ ] 支持更多文档格式（Word、PPT等）
- [ ] 添加OCR文字识别功能
- [ ] 实现文件版本管理
- [ ] 增强搜索和筛选功能
- [ ] 添加用户权限控制