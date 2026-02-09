<template>
  <div class="pdf-loader">
    <!-- 通知管理器 -->
    <NotificationManager />
    
    <!-- 加载遮罩 -->
    <LoadingOverlay 
      :is-loading="processing"
      :title="loadingTitle"
      :message="loadingMessage"
      :show-progress="showProgress"
      :progress="overallProgress"
      :current-file="currentFileName"
      :current-step="currentStep"
    />
    
    <!-- 文件预览模态框 -->
    <FilePreview 
      :show-preview="showPreview"
      :file-url="previewFileUrl"
      :file-name="previewFileName"
      :file-type="previewFileType"
      @close="closePreview"
      @download="handleDownload"
    />
    
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <div class="header-section">
              <div>
                <h4 class="card-title">PDF文档上传器</h4>
                <p class="text-muted">上传并处理PDF文档进行向量存储</p>
              </div>
              <div class="stats-badge">
                <span class="stat-item">
                  <i class="fa fa-file-pdf text-danger"></i>
                  {{ fileList.length }} 个文件
                </span>
                <span class="stat-item">
                  <i class="fa fa-database text-primary"></i>
                  {{ processedCount }} 已处理
                </span>
              </div>
            </div>
            
            <div class="upload-section">
              <div 
                class="upload-area" 
                :class="{ 'drag-over': isDragging, 'has-files': fileList.length > 0 }"
                @dragover.prevent="handleDragOver" 
                @dragenter.prevent="handleDragEnter"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop" 
                @click="triggerFileSelect"
              >
                <div class="upload-content">
                  <i class="fa fa-cloud-upload" :class="{ 'pulse': isDragging }"></i>
                  <h5>{{ dragText }}</h5>
                  <p>支持PDF格式，单个文件最大50MB</p>
                  <div class="file-types">
                    <span class="file-type-tag">.pdf</span>
                  </div>
                </div>
                <input 
                  type="file" 
                  ref="fileInput" 
                  @change="handleFileSelect" 
                  accept=".pdf,application/pdf" 
                  multiple 
                  style="display: none"
                />
              </div>
              
              <div class="upload-actions">
                <div class="action-buttons">
                  <button 
                    class="btn btn-primary" 
                    @click="processFiles" 
                    :disabled="fileList.length === 0 || processing"
                    :class="{ 'btn-loading': processing }"
                  >
                    <i class="fa fa-upload" v-if="!processing"></i>
                    <i class="fa fa-spinner fa-spin" v-else></i>
                    {{ processing ? '处理中...' : '开始处理' }}
                  </button>
                  <button 
                    class="btn btn-secondary" 
                    @click="clearFiles" 
                    :disabled="processing"
                  >
                    <i class="fa fa-trash"></i>
                    清空列表
                  </button>
                  <button 
                    class="btn btn-info" 
                    @click="loadHistory"
                    :disabled="processing"
                  >
                    <i class="fa fa-history"></i>
                    历史记录
                  </button>
                </div>
                
                <div class="upload-options" v-if="fileList.length > 0">
                  <div class="option-item">
                    <label>
                      <input type="checkbox" v-model="deduplicateEnabled" />
                      启用去重功能
                    </label>
                  </div>
                  <div class="option-item">
                    <label>集合名称:</label>
                    <input 
                      type="text" 
                      v-model="collectionName" 
                      placeholder="自动生成或手动输入"
                      class="form-control form-control-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-6">
        <div class="card">
          <div class="card-body">
            <div class="section-header">
              <h4 class="card-title">上传队列</h4>
              <div class="queue-stats">
                <span class="badge badge-pending" v-if="pendingCount > 0">
                  待处理: {{ pendingCount }}
                </span>
                <span class="badge badge-processing" v-if="processingCount > 0">
                  处理中: {{ processingCount }}
                </span>
                <span class="badge badge-completed" v-if="completedCount > 0">
                  已完成: {{ completedCount }}
                </span>
                <span class="badge badge-failed" v-if="failedCount > 0">
                  失败: {{ failedCount }}
                </span>
              </div>
            </div>
            
            <div class="file-list">
              <transition-group name="file-item" tag="div">
                <div 
                  v-for="(file, index) in fileList" 
                  :key="file.id" 
                  class="file-item"
                  :class="getFileItemClass(file.status)"
                >
                  <div class="file-info">
                    <div class="file-icon">
                      <i class="fa fa-file-pdf text-danger"></i>
                    </div>
                    <div class="file-details">
                      <h6>{{ file.name }}</h6>
                      <div class="file-meta">
                        <small class="file-size">{{ formatFileSize(file.size) }}</small>
                        <small class="file-date">{{ formatDate(file.lastModified) }}</small>
                      </div>
                      <div class="file-status-text" :class="getStatusClass(file.status)">
                        {{ getStatusText(file.status) }}
                        <span v-if="file.progress > 0 && file.status === 'processing'">
                          ({{ file.progress }}%)
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="file-actions">
                    <div class="action-buttons">
                      <button 
                        class="action-btn preview-btn" 
                        @click="previewFile(file)"
                        title="预览文件"
                      >
                        <i class="fa fa-eye"></i>
                      </button>
                      <button 
                        class="action-btn" 
                        @click="removeFile(index)"
                        :disabled="file.status === 'processing' || processing"
                        title="移除文件"
                      >
                        <i class="fa fa-times"></i>
                      </button>
                    </div>
                    
                    <!-- 单文件进度条 -->
                    <div class="file-progress" v-if="file.status === 'processing'">
                      <div class="progress">
                        <div 
                          class="progress-bar" 
                          :style="{ width: file.progress + '%' }"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </transition-group>
              
              <div v-if="fileList.length === 0" class="empty-state">
                <i class="fa fa-cloud-upload"></i>
                <p>暂无待上传的文件</p>
                <small>点击上方区域或拖拽PDF文件到这里</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-lg-6">
        <div class="card">
          <div class="card-body">
            <div class="section-header">
              <h4 class="card-title">处理状态</h4>
              <div class="refresh-actions">
                <button 
                  class="btn btn-sm btn-outline-secondary" 
                  @click="refreshStats"
                  :disabled="processing"
                >
                  <i class="fa fa-refresh"></i>
                  刷新
                </button>
              </div>
            </div>
            
            <div class="status-panel">
              <!-- 整体进度 -->
              <div class="overall-progress" v-if="processing || processedCount > 0">
                <h5>整体进度</h5>
                <div class="progress-container">
                  <div class="progress">
                    <div 
                      class="progress-bar" 
                      :class="{ 'progress-bar-animated': processing }"
                      :style="{ width: overallProgress + '%' }"
                    ></div>
                  </div>
                  <div class="progress-info">
                    <span>{{ Math.round(overallProgress) }}%</span>
                    <span>{{ completedCount }}/{{ fileList.length }} 完成</span>
                  </div>
                </div>
              </div>
              
              <!-- 结果统计 -->
              <div class="results-summary" v-if="processedCount > 0 || failedCount > 0">
                <h5>处理结果</h5>
                <div class="result-stats">
                  <div class="stat-card success">
                    <i class="fa fa-check-circle"></i>
                    <div>
                      <div class="stat-number">{{ processedCount }}</div>
                      <div class="stat-label">成功</div>
                    </div>
                  </div>
                  <div class="stat-card failed">
                    <i class="fa fa-exclamation-circle"></i>
                    <div>
                      <div class="stat-number">{{ failedCount }}</div>
                      <div class="stat-label">失败</div>
                    </div>
                  </div>
                  <div class="stat-card total">
                    <i class="fa fa-file-pdf"></i>
                    <div>
                      <div class="stat-number">{{ fileList.length }}</div>
                      <div class="stat-label">总计</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 系统状态 -->
              <div class="system-status">
                <h5>系统状态</h5>
                <div class="status-grid">
                  <div class="status-item" :class="{ 'online': vectorDbStatus }">
                    <i class="fa" :class="vectorDbStatus ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'"></i>
                    <span>向量数据库</span>
                  </div>
                  <div class="status-item" :class="{ 'online': pdfParserStatus }">
                    <i class="fa" :class="pdfParserStatus ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'"></i>
                    <span>PDF解析器</span>
                  </div>
                  <div class="status-item" :class="{ 'online': embeddingStatus }">
                    <i class="fa" :class="embeddingStatus ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'"></i>
                    <span>嵌入模型</span>
                  </div>
                  <div class="status-item" :class="{ 'online': deduplicationStatus }">
                    <i class="fa" :class="deduplicationStatus ? 'fa-check-circle text-success' : 'fa-times-circle text-warning'"></i>
                    <span>去重功能</span>
                  </div>
                </div>
              </div>
              
              <!-- 最近活动 -->
              <div class="recent-activity" v-if="recentActivities.length > 0">
                <h5>最近活动</h5>
                <div class="activity-list">
                  <div 
                    v-for="activity in recentActivities.slice(0, 5)" 
                    :key="activity.id"
                    class="activity-item"
                  >
                    <div class="activity-icon" :class="activity.type">
                      <i :class="activity.icon"></i>
                    </div>
                    <div class="activity-content">
                      <p class="activity-message">{{ activity.message }}</p>
                      <small class="activity-time">{{ formatRelativeTime(activity.timestamp) }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '@/services/api.js';

export default {
  name: 'PDFLoaderView',
  data() {
    return {
      fileList: [],
      processing: false,
      processedCount: 0,
      failedCount: 0,
      progressPercentage: 0,
      progressMessage: 'Ready to process'
    }
  },
  methods: {
    handleDragOver(e) {
      e.preventDefault();
    },
    handleDrop(e) {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files);
      this.addFiles(files);
    },
    triggerFileSelect() {
      if (!this.processing) {
        this.$refs.fileInput.click();
      }
    },
    handleFileSelect(e) {
      const files = Array.from(e.target.files);
      this.addFiles(files);
    },
    addFiles(files) {
      files.forEach(file => {
        if (file.type === 'application/pdf') {
          this.fileList.push({
            name: file.name,
            size: file.size,
            file: file,
            status: 'pending'
          });
        } else {
          alert(`${file.name} is not a PDF file!`);
        }
      });
    },
    async processFiles() {
      if (this.fileList.length === 0) {
        alert('Please select at least one PDF file to process.');
        return;
      }

      this.processing = true;
      this.progressPercentage = 0;
      this.processedCount = 0;
      this.failedCount = 0;

      // 处理每个文件
      for (let i = 0; i < this.fileList.length; i++) {
        this.fileList[i].status = 'processing';
        await this.uploadFile(this.fileList[i]);
        
        // 更新进度
        this.progressPercentage = ((i + 1) / this.fileList.length) * 100;
        this.progressMessage = `Processing... ${i + 1}/${this.fileList.length}`;
      }
      
      this.progressMessage = 'Processing completed!';
      this.processing = false;
      
      setTimeout(() => {
        this.progressMessage = 'Ready to process';
      }, 3000);
    },
    async uploadFile(fileObj) {
      const formData = new FormData();
      formData.append('file', fileObj.file);
      formData.append('title', fileObj.name);
      // 默认使用第一个Milvus连接和动态生成的集合名称
      formData.append('milvus_connection_id', 1); 
      formData.append('collection_name', 'pdf_docs_' + Date.now());

      try {
        const response = await pdfLoaderAPI.uploadPDF(formData);
        
        if (response.data.success) {
          fileObj.status = 'completed';
          fileObj.result = response.data.data; // 保存处理结果
          this.processedCount++;
          // 显示成功消息
          this.showSuccessMessage(`文件 ${fileObj.name} 上传成功`);
        } else {
          fileObj.status = 'failed';
          fileObj.error = response.data.message;
          this.failedCount++;
          this.showErrorMessage(`文件 ${fileObj.name} 上传失败: ${response.data.message}`);
        }
      } catch (error) {
        console.error('Upload error:', error);
        fileObj.status = 'failed';
        fileObj.error = error.message;
        this.failedCount++;
        this.showErrorMessage(`文件 ${fileObj.name} 上传异常: ${error.message}`);
      }
    },
    removeFile(index) {
      if (!this.processing) {
        this.fileList.splice(index, 1);
      }
    },
    clearFiles() {
      if (!this.processing) {
        this.fileList = [];
        this.processedCount = 0;
        this.failedCount = 0;
      }
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    getStatusClass(status) {
      switch (status) {
        case 'completed': return 'status-completed';
        case 'failed': return 'status-failed';
        case 'processing': return 'status-processing';
        default: return 'status-pending';
      }
    }
  }
}
</script>

<style scoped>
.pdf-loader {
  padding: 20px 0;
}

.card {
  border: none;
  border-radius: 8px;
  box-shadow: 0 3px 15px rgba(0,0,0,0.1);
  margin-bottom: 25px;
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.card-body {
  padding: 1.5rem;
}

/* 头部区域 */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 15px;
}

.stats-badge {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

/* 上传区域 */
.upload-section {
  margin-bottom: 30px;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
  position: relative;
  overflow: hidden;
}

.upload-area:hover {
  border-color: #3498DB;
  background: #f0f8ff;
  transform: translateY(-2px);
}

.upload-area.drag-over {
  border-color: #3498DB;
  background: #e3f2fd;
  transform: scale(1.02);
}

.upload-area.has-files {
  border-color: #28a745;
  background: #f0fff4;
}

.upload-content i {
  font-size: 48px;
  color: #ccc;
  margin-bottom: 15px;
  transition: all 0.3s ease;
}

.upload-area:hover .upload-content i,
.upload-area.drag-over .upload-content i {
  color: #3498DB;
  transform: scale(1.1);
}

.upload-content i.pulse {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.upload-content h5 {
  margin-bottom: 10px;
  color: #333;
  font-weight: 500;
}

.upload-content p {
  color: #666;
  margin-bottom: 15px;
  font-size: 14px;
}

.file-types {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-type-tag {
  background: #3498DB;
  color: white;
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 500;
}

/* 操作按钮区域 */
.upload-actions {
  margin-top: 25px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.upload-options {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  align-items: center;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-item label {
  margin: 0;
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.form-control-sm {
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

/* 按钮样式 */
.btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  font-weight: 500;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-loading {
  position: relative;
}

.btn-primary {
  background: linear-gradient(135deg, #3498DB, #2980B9);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2980B9, #2573A7);
}

.btn-secondary {
  background: linear-gradient(135deg, #95a5a6, #7f8c8d);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #7f8c8d, #6c7a7b);
}

.btn-info {
  background: linear-gradient(135deg, #17a2b8, #138496);
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: linear-gradient(135deg, #138496, #10707f);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-outline-secondary {
  background: transparent;
  border: 1px solid #6c757d;
  color: #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background: #6c757d;
  color: white;
}

/* 文件列表 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.queue-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.badge {
  padding: 6px 12px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 500;
}

.badge-pending {
  background: #fff3cd;
  color: #856404;
}

.badge-processing {
  background: #cce5ff;
  color: #004085;
}

.badge-completed {
  background: #d4edda;
  color: #155724;
}

.badge-failed {
  background: #f8d7da;
  color: #721c24;
}

.file-list {
  max-height: 500px;
  overflow-y: auto;
}

/* 文件项动画 */
.file-item-enter-active,
.file-item-leave-active {
  transition: all 0.3s ease;
}

.file-item-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.file-item-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
  transition: all 0.2s ease;
}

.file-item:hover {
  background: #f8f9fa;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item-processing {
  background: #e3f2fd;
  border-left: 3px solid #3498DB;
}

.file-item-completed {
  background: #f0fff4;
  border-left: 3px solid #28a745;
}

.file-item-failed {
  background: #fff5f5;
  border-left: 3px solid #dc3545;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.file-icon {
  margin-right: 15px;
}

.file-icon i {
  font-size: 24px;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-details h6 {
  margin: 0 0 5px 0;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 5px;
}

.file-size, .file-date {
  color: #666;
  font-size: 12px;
}

.file-status-text {
  font-size: 13px;
  font-weight: 500;
}

.file-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  min-width: 120px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f0f0f0;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: #3498DB;
  color: white;
  transform: scale(1.1);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-btn {
  background: #e3f2fd;
  color: #3498DB;
}

.preview-btn:hover:not(:disabled) {
  background: #3498DB;
  color: white;
}

.file-progress {
  width: 100px;
}

.file-progress .progress {
  height: 6px;
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #ddd;
}

.empty-state p {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 500;
}

.empty-state small {
  color: #bbb;
}

/* 状态面板 */
.status-panel {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.overall-progress h5,
.results-summary h5,
.system-status h5,
.recent-activity h5 {
  margin: 0 0 15px 0;
  color: #333;
  font-weight: 600;
  font-size: 16px;
}

.refresh-actions {
  display: flex;
  gap: 10px;
}

/* 整体进度 */
.progress-container {
  margin-bottom: 15px;
}

.progress {
  height: 12px;
  background-color: #e9ecef;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3498DB, #28a745);
  border-radius: 6px;
  transition: width 0.3s ease;
}

.progress-bar-animated {
  animation: progress-pulse 2s ease-in-out infinite alternate;
}

@keyframes progress-pulse {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #666;
}

/* 结果统计 */
.result-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 15px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  background: #f8f9fa;
}

.stat-card.success {
  background: #d4edda;
  border-left: 4px solid #28a745;
}

.stat-card.failed {
  background: #f8d7da;
  border-left: 4px solid #dc3545;
}

.stat-card.total {
  background: #cce5ff;
  border-left: 4px solid #3498DB;
}

.stat-card i {
  font-size: 24px;
}

.stat-card.success i {
  color: #28a745;
}

.stat-card.failed i {
  color: #dc3545;
}

.stat-card.total i {
  color: #3498DB;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

/* 系统状态 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 6px;
  background: #f8f9fa;
  font-size: 13px;
  font-weight: 500;
}

.status-item.online {
  background: #d4edda;
}

.status-item.offline {
  background: #f8d7da;
}

/* 最近活动 */
.activity-list {
  max-height: 200px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-icon.success {
  background: #d4edda;
  color: #28a745;
}

.activity-icon.error {
  background: #f8d7da;
  color: #dc3545;
}

.activity-icon.warning {
  background: #fff3cd;
  color: #ffc107;
}

.activity-icon.info {
  background: #cce5ff;
  color: #3498DB;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-message {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #333;
}

.activity-time {
  font-size: 12px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stats-badge {
    justify-content: center;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .upload-options {
    flex-direction: column;
    align-items: stretch;
  }
  
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .queue-stats {
    justify-content: center;
  }
  
  .file-item {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .file-actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    min-width: auto;
  }
  
  .result-stats {
    grid-template-columns: 1fr 1fr;
  }
  
  .status-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .pdf-loader {
    padding: 10px 0;
  }
  
  .card-body {
    padding: 1rem;
  }
  
  .upload-area {
    padding: 25px 15px;
  }
  
  .result-stats,
  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>

.file-list {
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
}

.file-info i {
  font-size: 24px;
  color: #E74C3C;
  margin-right: 15px;
}

.file-details h6 {
  margin: 0;
  font-weight: 500;
}

.file-details small {
  color: #999;
}

.file-status {
  display: flex;
  align-items: center;
}

.status-pending {
  color: #F39C12;
}

.status-processing {
  color: #3498DB;
}

.status-completed {
  color: #27AE60;
}

.status-failed {
  color: #E74C3C;
}

.remove-btn {
  background: none;
  border: none;
  color: #E74C3C;
  cursor: pointer;
  margin-left: 15px;
  font-size: 16px;
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #999;
}

.progress-container {
  margin-bottom: 20px;
}

.progress {
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background-color: #3498DB;
  transition: width 0.3s;
}

.results {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.status-info ul {
  list-style: none;
  padding: 0;
}

.status-info li {
  margin-bottom: 10px;
}

.text-success {
  color: #27AE60;
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10px;
}

.col-lg-6 {
  position: relative;
  width: 100%;
  padding: 0 10px;
  flex: 0 0 50%;
  max-width: 50%;
}

@media (max-width: 991px) {
  .col-lg-6 {
    flex: 0 0 100%;
    max-width: 100%;
  }
}
</style>