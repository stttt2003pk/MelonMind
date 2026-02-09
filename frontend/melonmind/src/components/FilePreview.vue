<template>
  <div class="file-preview-overlay" @click="closePreview" v-if="showPreview">
    <div class="preview-container" @click.stop>
      <div class="preview-header">
        <h4>{{ fileName }}</h4>
        <div class="preview-actions">
          <button class="btn btn-sm btn-outline-secondary" @click="downloadFile" v-if="fileUrl">
            <i class="fa fa-download"></i> 下载
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="printFile" v-if="canPrint">
            <i class="fa fa-print"></i> 打印
          </button>
          <button class="btn btn-sm btn-close" @click="closePreview">
            <i class="fa fa-times"></i>
          </button>
        </div>
      </div>
      
      <div class="preview-content">
        <!-- PDF预览 -->
        <div v-if="fileType === 'pdf'" class="pdf-preview">
          <div v-if="loading" class="loading-indicator">
            <div class="spinner"></div>
            <p>正在加载PDF...</p>
          </div>
          
          <div v-else-if="error" class="error-message">
            <i class="fa fa-exclamation-triangle"></i>
            <p>{{ error }}</p>
            <button class="btn btn-primary" @click="retryLoad">重试</button>
          </div>
          
          <div v-else class="pdf-viewer">
            <div class="pdf-controls">
              <button 
                class="btn btn-sm btn-outline-primary" 
                @click="prevPage" 
                :disabled="currentPage <= 1"
              >
                <i class="fa fa-arrow-left"></i>
              </button>
              <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
              <button 
                class="btn btn-sm btn-outline-primary" 
                @click="nextPage" 
                :disabled="currentPage >= totalPages"
              >
                <i class="fa fa-arrow-right"></i>
              </button>
              
              <div class="zoom-controls">
                <button class="btn btn-sm btn-outline-secondary" @click="zoomOut">
                  <i class="fa fa-search-minus"></i>
                </button>
                <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
                <button class="btn btn-sm btn-outline-secondary" @click="zoomIn">
                  <i class="fa fa-search-plus"></i>
                </button>
              </div>
            </div>
            
            <div class="pdf-pages">
              <canvas 
                ref="pdfCanvas" 
                class="pdf-page"
                :style="{ transform: `scale(${zoom})` }"
              ></canvas>
            </div>
          </div>
        </div>
        
        <!-- 图片预览 -->
        <div v-else-if="fileType === 'image'" class="image-preview">
          <div class="image-container">
            <img 
              :src="fileUrl" 
              :alt="fileName"
              :style="{ 
                transform: `scale(${zoom}) rotate(${rotation}deg)`,
                maxWidth: zoom > 1 ? '100%' : 'auto'
              }"
              @load="onImageLoad"
              @error="onImageError"
            />
          </div>
          
          <div class="image-controls">
            <button class="btn btn-sm btn-outline-secondary" @click="rotateLeft">
              <i class="fa fa-undo"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="rotateRight">
              <i class="fa fa-repeat"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="zoomOut">
              <i class="fa fa-search-minus"></i>
            </button>
            <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
            <button class="btn btn-sm btn-outline-secondary" @click="zoomIn">
              <i class="fa fa-search-plus"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="resetView">
              <i class="fa fa-refresh"></i>
            </button>
          </div>
        </div>
        
        <!-- 文本文件预览 -->
        <div v-else-if="fileType === 'text'" class="text-preview">
          <div v-if="loading" class="loading-indicator">
            <div class="spinner"></div>
            <p>正在加载文本...</p>
          </div>
          
          <div v-else-if="textContent" class="text-content">
            <pre>{{ textContent }}</pre>
          </div>
          
          <div v-else class="error-message">
            <i class="fa fa-file-text"></i>
            <p>无法预览此文本文件</p>
          </div>
        </div>
        
        <!-- 不支持的文件类型 -->
        <div v-else class="unsupported-preview">
          <i class="fa fa-file"></i>
          <h5>不支持的文件类型</h5>
          <p>该文件类型暂不支持在线预览</p>
          <button class="btn btn-primary" @click="downloadFile">下载文件</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue';
// 注意：vue3-pdfjs 需要正确导入
// import { usePDF } from 'vue3-pdfjs/composables';

export default {
  name: 'FilePreview',
  props: {
    showPreview: {
      type: Boolean,
      default: false
    },
    fileUrl: {
      type: String,
      default: ''
    },
    fileName: {
      type: String,
      default: ''
    },
    fileType: {
      type: String,
      default: 'pdf' // pdf, image, text
    }
  },
  emits: ['close', 'download'],
  setup(props, { emit }) {
    // PDF 相关状态
    const pdfDoc = ref(null);
    const currentPage = ref(1);
    const totalPages = ref(0);
    
    // 显示控制
    const loading = ref(false);
    const error = ref('');
    
    // 视图控制
    const zoom = ref(1);
    const rotation = ref(0);
    const textContent = ref('');
    
    // Canvas引用
    const pdfCanvas = ref(null);
    
    // 计算属性
    const canPrint = computed(() => {
      return props.fileType === 'pdf' || props.fileType === 'image';
    });
    
    // 方法定义
    const closePreview = () => {
      emit('close');
    };
    
    const downloadFile = () => {
      if (props.fileUrl) {
        const link = document.createElement('a');
        link.href = props.fileUrl;
        link.download = props.fileName;
        link.click();
        emit('download', props.fileName);
      }
    };
    
    const printFile = () => {
      if (props.fileType === 'pdf') {
        // PDF打印逻辑
        window.print();
      } else if (props.fileType === 'image') {
        // 图片打印逻辑
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
          <html>
            <head>
              <title>${props.fileName}</title>
            </head>
            <body style="margin:0;padding:20px;">
              <img src="${props.fileUrl}" style="max-width:100%;" onload="window.print()" />
            </body>
          </html>
        `);
        printWindow.document.close();
      }
    };
    
    // PDF 控制方法
    const loadPDF = async () => {
      if (!props.fileUrl || props.fileType !== 'pdf') return;
      
      loading.value = true;
      error.value = '';
      
      try {
        // 使用原生PDF.js或其他PDF库
        // 这里简化处理，实际需要引入PDF.js库
        
        // 模拟PDF加载
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 设置总页数（模拟）
        totalPages.value = 5;
        renderPDFPage();
        
      } catch (err) {
        error.value = 'PDF加载失败';
        console.error('PDF load error:', err);
      } finally {
        loading.value = false;
      }
    };
    
    const renderPDFPage = async () => {
      if (!pdfCanvas.value || !pdfDoc.value) return;
      
      try {
        // 渲染PDF页面到canvas
        // 这里是简化版本，实际需要PDF.js的具体实现
        const canvas = pdfCanvas.value;
        const ctx = canvas.getContext('2d');
        
        // 设置canvas尺寸
        canvas.width = 800;
        canvas.height = 1000;
        
        // 清空画布
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 绘制示例内容
        ctx.fillStyle = '#333333';
        ctx.font = '20px Arial';
        ctx.fillText(`第 ${currentPage.value} 页`, 50, 50);
        ctx.fillText('PDF预览功能占位符', 50, 100);
        
      } catch (err) {
        console.error('PDF render error:', err);
      }
    };
    
    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--;
        renderPDFPage();
      }
    };
    
    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++;
        renderPDFPage();
      }
    };
    
    // 图片控制方法
    const rotateLeft = () => {
      rotation.value = (rotation.value - 90) % 360;
    };
    
    const rotateRight = () => {
      rotation.value = (rotation.value + 90) % 360;
    };
    
    const zoomIn = () => {
      zoom.value = Math.min(zoom.value + 0.1, 3);
    };
    
    const zoomOut = () => {
      zoom.value = Math.max(zoom.value - 0.1, 0.1);
    };
    
    const resetView = () => {
      zoom.value = 1;
      rotation.value = 0;
    };
    
    const onImageLoad = () => {
      loading.value = false;
      error.value = '';
    };
    
    const onImageError = () => {
      loading.value = false;
      error.value = '图片加载失败';
    };
    
    const retryLoad = () => {
      if (props.fileType === 'pdf') {
        loadPDF();
      }
    };
    
    // 监听属性变化
    watch(() => props.showPreview, (newVal) => {
      if (newVal) {
        nextTick(() => {
          if (props.fileType === 'pdf') {
            loadPDF();
          } else if (props.fileType === 'text') {
            loadTextFile();
          }
        });
      } else {
        // 重置状态
        currentPage.value = 1;
        zoom.value = 1;
        rotation.value = 0;
        textContent.value = '';
        error.value = '';
      }
    });
    
    const loadTextFile = async () => {
      if (!props.fileUrl || props.fileType !== 'text') return;
      
      loading.value = true;
      try {
        const response = await fetch(props.fileUrl);
        textContent.value = await response.text();
      } catch (err) {
        error.value = '文本文件加载失败';
      } finally {
        loading.value = false;
      }
    };
    
    return {
      // 状态
      pdfDoc,
      currentPage,
      totalPages,
      loading,
      error,
      zoom,
      rotation,
      textContent,
      pdfCanvas,
      canPrint,
      
      // 方法
      closePreview,
      downloadFile,
      printFile,
      prevPage,
      nextPage,
      rotateLeft,
      rotateRight,
      zoomIn,
      zoomOut,
      resetView,
      onImageLoad,
      onImageError,
      retryLoad
    };
  }
};
</script>

<style scoped>
.file-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.preview-container {
  background: white;
  border-radius: 8px;
  width: 90%;
  height: 90%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.preview-header h4 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.preview-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.btn:hover {
  background: #f0f0f0;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

.btn-outline-secondary {
  border-color: #6c757d;
  color: #6c757d;
}

.btn-outline-primary {
  border-color: #007bff;
  color: #007bff;
}

.btn-primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.btn-close {
  border: none;
  background: #dc3545;
  color: white;
}

.preview-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* PDF预览样式 */
.pdf-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pdf-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.page-info {
  min-width: 80px;
  text-align: center;
  font-weight: 500;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.zoom-value {
  min-width: 60px;
  text-align: center;
}

.pdf-pages {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
  background: #eee;
}

.pdf-page {
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-width: 100%;
}

/* 图片预览样式 */
.image-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.image-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
  padding: 20px;
  background: #f0f0f0;
}

.image-container img {
  max-width: 100%;
  max-height: 100%;
  transition: transform 0.2s ease;
}

.image-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  border-top: 1px solid #eee;
  background: #f8f9fa;
  justify-content: center;
}

/* 文本预览样式 */
.text-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.text-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.text-content pre {
  margin: 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 加载和错误状态 */
.loading-indicator {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #dc3545;
  text-align: center;
  padding: 20px;
}

.error-message i {
  font-size: 48px;
  margin-bottom: 15px;
}

.unsupported-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: #666;
  padding: 20px;
}

.unsupported-preview i {
  font-size: 64px;
  margin-bottom: 20px;
  color: #999;
}

.unsupported-preview h5 {
  margin-bottom: 10px;
  color: #333;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-container {
    width: 95%;
    height: 95%;
  }
  
  .preview-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .preview-actions {
    width: 100%;
    justify-content: center;
  }
  
  .pdf-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .zoom-controls {
    margin-left: 0;
    margin-top: 10px;
  }
}
</style>