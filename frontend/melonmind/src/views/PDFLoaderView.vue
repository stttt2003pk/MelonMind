<template>
  <div class="pdf-loader">
    <!-- 文件预览模态框 -->
    <FilePreview 
      :show-preview="showPreview"
      :file-url="previewFileUrl"
      :file-name="previewFileName"
      :file-type="previewFileType"
      @close="closePreview"
    />
    
    <!-- 基础上传区域 -->
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
              </div>
            </div>
            
            <div class="upload-section">
              <div 
                class="upload-area" 
                :class="{ 'drag-over': isDragging }"
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
                    <i class="fa fa-spinner fa-spin" v-if="processing"></i>
                    <i class="fa fa-upload" v-else></i>
                    {{ processing ? '处理中...' : '开始处理' }}
                  </button>
                  <button 
                    class="btn btn-secondary" 
                    @click="clearFiles"
                  >
                    <i class="fa fa-trash"></i>
                    清空列表
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 文件列表 -->
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h4 class="card-title">上传队列</h4>
            <div class="file-list">
              <div 
                v-for="(file, index) in fileList" 
                :key="file.id" 
                class="file-item"
              >
                <div class="file-info">
                  <div class="file-icon">
                    <i class="fa fa-file-pdf text-danger"></i>
                  </div>
                  <div class="file-details">
                    <h6>{{ file.name }}</h6>
                    <div class="file-status">
                      <span class="status-badge" :class="file.status">
                        {{ getStatusText(file.status) }}
                      </span>
                      <div class="progress-bar" v-if="file.status === 'processing'">
                        <div class="progress-fill" :style="{ width: file.progress + '%' }"></div>
                      </div>
                      <span v-if="file.progress > 0 && file.status === 'processing'" class="progress-text">
                        {{ file.progress }}%
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
                      title="移除文件"
                    >
                      <i class="fa fa-times"></i>
                    </button>
                  </div>
                </div>
              </div>
              
              <div v-if="fileList.length === 0" class="empty-state">
                <i class="fa fa-file-alt"></i>
                <p>暂无文件，请上传PDF文档</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { pdfLoaderAPI, knowledgeBaseAPI } from '@/services/api'
import FilePreview from '@/components/FilePreview.vue'

export default {
  name: 'PDFLoaderView',
  components: {
    FilePreview
  },
  setup() {
    // 响应式数据
    const fileList = ref([])
    const isDragging = ref(false)
    const fileInput = ref(null)
    const processing = ref(false)
    
    // 预览相关数据
    const showPreview = ref(false)
    const previewFileUrl = ref('')
    const previewFileName = ref('')
    const previewFileType = ref('')
    
    // 计算属性
    const dragText = computed(() => {
      return isDragging.value ? '释放文件开始上传' : '拖拽PDF文件到此处或点击选择文件'
    })
    
    // 方法
    const handleDragOver = (event) => {
      event.preventDefault()
      isDragging.value = true
    }
    
    const handleDragEnter = (event) => {
      event.preventDefault()
      isDragging.value = true
    }
    
    const handleDragLeave = (event) => {
      event.preventDefault()
      isDragging.value = false
    }
    
    const handleDrop = (event) => {
      event.preventDefault()
      isDragging.value = false
      
      const files = Array.from(event.dataTransfer.files)
      handleFiles(files)
    }
    
    const triggerFileSelect = () => {
      if (fileInput.value) {
        fileInput.value.click()
      }
    }
    
    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      handleFiles(files)
    }
    
    const handleFiles = (files) => {
      files.forEach(file => {
        if (file.type === 'application/pdf' && file.size <= 50 * 1024 * 1024) {
          const fileItem = {
            id: Date.now() + Math.random(),
            name: file.name,
            size: file.size,
            lastModified: file.lastModified,
            file: file,
            status: 'pending',
            progress: 0
          }
          fileList.value.push(fileItem)
        }
      })
    }
    
    const removeFile = (index) => {
      fileList.value.splice(index, 1)
    }
    
    const clearFiles = () => {
      fileList.value = []
    }
    
    const processFiles = async () => {
      if (fileList.value.length === 0) return
      
      processing.value = true
      
      try {
        // 逐个处理文件
        for (let i = 0; i < fileList.value.length; i++) {
          const file = fileList.value[i]
          file.status = 'processing'
          file.progress = 0
          
          try {
            // 调用后端API上传文件
            const formData = new FormData()
            formData.append('file', file.file)
            formData.append('title', file.name.replace('.pdf', ''))
            formData.append('milvus_connection_id', '1')
            formData.append('collection_name', `pdf_docs_${Date.now()}`)
            
            const response = await pdfLoaderAPI.uploadPDF(formData, (percentCompleted) => {
              // 更新上传进度
              file.progress = percentCompleted
            })
            
            if (response.success) {
              file.status = 'completed'
              file.progress = 100
              console.log(`文件 ${file.name} 上传成功:`, response.data)
            } else {
              throw new Error(response.message || '上传失败')
            }
          } catch (error) {
            console.error(`文件 ${file.name} 上传失败:`, error)
            file.status = 'failed'
            file.progress = 0
          }
        }
        
        // 获取最新的统计信息
        try {
          const stats = await knowledgeBaseAPI.getDocumentStats()
          console.log('文档统计:', stats)
        } catch (error) {
          console.error('获取统计信息失败:', error)
        }
        
        const successCount = fileList.value.filter(f => f.status === 'completed').length
        alert(`处理完成！成功: ${successCount}/${fileList.value.length} 个文件`)
        
      } catch (error) {
        console.error('处理文件时出错:', error)
        alert('处理文件时出现错误: ' + error.message)
      } finally {
        processing.value = false
      }
    }
    
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
      }
      return statusMap[status] || status
    }
    
    const previewFile = (file) => {
      // 创建文件URL用于预览
      const url = URL.createObjectURL(file.file)
      previewFileUrl.value = url
      previewFileName.value = file.name
      previewFileType.value = file.file.type
      showPreview.value = true
    }
    
    const closePreview = () => {
      showPreview.value = false
      // 清理创建的URL
      if (previewFileUrl.value) {
        URL.revokeObjectURL(previewFileUrl.value)
        previewFileUrl.value = ''
      }
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    return {
      // 数据
      fileList,
      isDragging,
      fileInput,
      processing,
      showPreview,
      previewFileUrl,
      previewFileName,
      previewFileType,
      
      // 计算属性
      dragText,
      
      // 方法
      handleDragOver,
      handleDragEnter,
      handleDragLeave,
      handleDrop,
      triggerFileSelect,
      handleFileSelect,
      removeFile,
      clearFiles,
      processFiles,
      formatFileSize,
      getStatusText,
      previewFile,
      closePreview
    }
  }
}
</script>

<style scoped>
.pdf-loader {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.card-body {
  padding: 20px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.text-muted {
  color: #6c757d;
  margin: 5px 0 0 0;
}

.stats-badge {
  display: flex;
  gap: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  background: #f8f9fa;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.9rem;
}

.upload-section {
  margin-bottom: 20px;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.upload-area:hover {
  border-color: #007bff;
  background-color: #f0f8ff;
}

.upload-area.drag-over {
  border-color: #007bff;
  background-color: #e3f2fd;
  transform: scale(1.02);
}

.upload-content {
  color: #666;
}

.upload-content i {
  font-size: 3rem;
  color: #007bff;
  margin-bottom: 15px;
  display: block;
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
  font-size: 1.2rem;
  margin: 10px 0;
  color: #333;
}

.upload-content p {
  margin: 5px 0;
  color: #666;
}

.file-types {
  margin-top: 10px;
}

.file-type-tag {
  background: #007bff;
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
}

.upload-actions {
  margin-top: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.8rem;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-loading {
  opacity: 0.8;
}

.btn-loading .fa-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.file-status {
  margin-top: 8px;
}

.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.pending {
  background-color: #ffc107;
  color: #212529;
}

.status-badge.processing {
  background-color: #17a2b8;
  color: white;
}

.status-badge.completed {
  background-color: #28a745;
  color: white;
}

.status-badge.failed {
  background-color: #dc3545;
  color: white;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 3px;
  margin: 5px 0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #007bff;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.action-buttons {
  display: flex;
  gap: 5px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: #f8f9fa;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #e9ecef;
  color: #333;
  transform: scale(1.1);
}

.preview-btn {
  background: #007bff;
  color: white;
}

.preview-btn:hover {
  background: #0056b3;
  color: white;
}

.progress-text {
  font-size: 0.8rem;
  color: #666;
  margin-left: 5px;
}

.file-list {
  min-height: 100px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 10px;
  background: white;
  transition: all 0.2s ease;
}

.file-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.file-icon {
  margin-right: 15px;
  font-size: 1.5rem;
}

.file-details h6 {
  margin: 0 0 5px 0;
  font-size: 1rem;
  color: #333;
}

.file-meta {
  display: flex;
  gap: 15px;
}

.file-size {
  color: #666;
  font-size: 0.85rem;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 15px;
  color: #ccc;
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10px;
}

.col-12 {
  width: 100%;
  padding: 0 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .pdf-loader {
    padding: 10px;
  }
  
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .stats-badge {
    width: 100%;
    justify-content: space-between;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>