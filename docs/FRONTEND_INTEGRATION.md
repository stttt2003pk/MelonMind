# MelonMind 前端集成指南

## 文档统计 API 集成

### API 端点

- **URL**: `/api/knowledge/document-stats/`
- **方法**: `GET`
- **认证**: 无需认证（公开访问）
- **内容类型**: `application/json`

### 响应格式

```json
{
  "total_documents": 0,
  "processed_documents": 0,
  "processing_documents": 0,
  "failed_documents": 0,
  "uploaded_documents": 0
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `total_documents` | 整数 | 系统中总文档数量 |
| `processed_documents` | 整数 | 已成功处理的文档数量（已完成向量化的文档） |
| `processing_documents` | 整数 | 当前正在处理的文档数量 |
| `failed_documents` | 整数 | 处理失败的文档数量 |
| `uploaded_documents` | 整数 | 已上传但尚未开始处理的文档数量 |

### 前端集成示例

#### JavaScript 示例

```javascript
// 获取文档统计信息
async function fetchDocumentStats() {
  try {
    const response = await fetch('/api/knowledge/document-stats/');
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Document stats:', data);
    
    // 更新UI
    updateDocumentStatsUI(data);
    
    return data;
  } catch (error) {
    console.error('Error fetching document stats:', error);
    // 显示错误消息给用户
    showErrorNotification('无法获取文档统计信息');
  }
}

// 更新UI的函数
function updateDocumentStatsUI(stats) {
  document.getElementById('total-documents-count').textContent = stats.total_documents;
  document.getElementById('processed-documents-count').textContent = stats.processed_documents;
  document.getElementById('processing-documents-count').textContent = stats.processing_documents;
  document.getElementById('failed-documents-count').textContent = stats.failed_documents;
  document.getElementById('uploaded-documents-count').textContent = stats.uploaded_documents;
  
  // 计算进度百分比
  if (stats.total_documents > 0) {
    const processingPercent = (stats.processing_documents / stats.total_documents) * 100;
    const failedPercent = (stats.failed_documents / stats.total_documents) * 100;
    const processedPercent = (stats.processed_documents / stats.total_documents) * 100;
    
    // 更新进度条
    updateProgressBar(processedPercent, processingPercent, failedPercent);
  }
}

// 页面加载时获取数据
document.addEventListener('DOMContentLoaded', function() {
  fetchDocumentStats();
});
```

#### Vue.js 组件示例

```vue
<template>
  <div class="document-stats">
    <h3>文档统计</h3>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_documents }}</div>
        <div class="stat-label">总文档数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.processed_documents }}</div>
        <div class="stat-label">已处理</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.processing_documents }}</div>
        <div class="stat-label">处理中</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.failed_documents }}</div>
        <div class="stat-label">失败</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.uploaded_documents }}</div>
        <div class="stat-label">已上传</div>
      </div>
    </div>
    
    <!-- 进度条 -->
    <div class="progress-container" v-if="stats.total_documents > 0">
      <div class="progress-bar">
        <div class="progress-fill processed" 
             :style="{ width: processedPercent + '%' }"></div>
        <div class="progress-fill processing" 
             :style="{ width: processingPercent + '%' }"></div>
        <div class="progress-fill failed" 
             :style="{ width: failedPercent + '%' }"></div>
      </div>
      <div class="progress-labels">
        <span>{{ processedPercent }}% 已处理</span>
        <span>{{ processingPercent }}% 处理中</span>
        <span>{{ failedPercent }}% 失败</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentStats',
  data() {
    return {
      stats: {
        total_documents: 0,
        processed_documents: 0,
        processing_documents: 0,
        failed_documents: 0,
        uploaded_documents: 0
      }
    }
  },
  computed: {
    processedPercent() {
      if (this.stats.total_documents === 0) return 0;
      return Math.round((this.stats.processed_documents / this.stats.total_documents) * 100);
    },
    processingPercent() {
      if (this.stats.total_documents === 0) return 0;
      return Math.round((this.stats.processing_documents / this.stats.total_documents) * 100);
    },
    failedPercent() {
      if (this.stats.total_documents === 0) return 0;
      return Math.round((this.stats.failed_documents / this.stats.total_documents) * 100);
    }
  },
  mounted() {
    this.loadStats();
    // 每30秒自动刷新一次
    setInterval(this.loadStats, 30000);
  },
  methods: {
    async loadStats() {
      try {
        const response = await fetch('/api/knowledge/document-stats/');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        this.stats = await response.json();
      } catch (error) {
        console.error('Failed to load document stats:', error);
      }
    }
  }
}
</script>

<style scoped>
.document-stats {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.stat-card {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
}

.stat-label {
  font-size: 14px;
  color: #6c757d;
  margin-top: 4px;
}

.progress-container {
  margin-top: 20px;
}

.progress-bar {
  height: 24px;
  background: #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
}

.progress-fill {
  height: 100%;
}

.processed { background: #28a745; }
.processing { background: #ffc107; }
.failed { background: #dc3545; }

.progress-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #6c757d;
}
</style>
```

### 错误处理

前端应处理以下可能的错误情况：

1. **网络错误**: 服务器不可达
2. **HTTP错误**: 服务器返回非200状态码
3. **数据格式错误**: 响应不是有效的JSON

### 自动刷新建议

由于文档状态可能会随时间变化（例如，文档从"处理中"变为"已完成"），建议前端实现定期轮询：

```javascript
// 每30秒刷新一次统计数据
const refreshInterval = setInterval(fetchDocumentStats, 30000);

// 在组件卸载时清除定时器
window.addEventListener('beforeunload', () => {
  clearInterval(refreshInterval);
});
```

### 权限说明

此API端点是公开的，无需身份验证。这意味着任何用户都可以访问文档统计信息，这对于显示系统状态是有意义的，但在敏感环境中可能需要额外的安全考虑。

### 性能考虑

- API响应通常很小（少于1KB），不会造成显著的网络负载
- 建议设置适当的轮询间隔（如30秒），避免过于频繁的请求
- 对于高并发场景，可考虑在前端实现缓存机制