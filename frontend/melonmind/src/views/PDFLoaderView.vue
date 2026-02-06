<template>
  <div class="pdf-loader">
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h4 class="card-title">PDF Document Loader</h4>
            <p class="text-muted">Upload and process PDF documents for vector storage</p>
            
            <div class="upload-section">
              <div class="upload-area" @dragover.prevent="handleDragOver" @drop.prevent="handleDrop" @click="triggerFileSelect">
                <div class="upload-content">
                  <i class="fa fa-cloud-upload"></i>
                  <h5>Drag & Drop your PDF files here</h5>
                  <p>or click to browse files</p>
                </div>
                <input 
                  type="file" 
                  ref="fileInput" 
                  @change="handleFileSelect" 
                  accept=".pdf" 
                  multiple 
                  style="display: none"
                >
              </div>
              
              <div class="upload-actions">
                <button class="btn btn-primary" @click="processFiles">Process Files</button>
                <button class="btn btn-secondary" @click="clearFiles">Clear All</button>
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
            <h4 class="card-title">Upload Queue</h4>
            <div class="file-list">
              <div 
                v-for="(file, index) in fileList" 
                :key="index" 
                class="file-item"
              >
                <div class="file-info">
                  <i class="fa fa-file-pdf"></i>
                  <div class="file-details">
                    <h6>{{ file.name }}</h6>
                    <small>{{ formatFileSize(file.size) }}</small>
                  </div>
                </div>
                <div class="file-status">
                  <span :class="getStatusClass(file.status)">{{ file.status }}</span>
                  <button 
                    class="remove-btn" 
                    @click="removeFile(index)"
                    v-if="file.status !== 'processing' && file.status !== 'completed'"
                  >
                    <i class="fa fa-times"></i>
                  </button>
                </div>
              </div>
              
              <div v-if="fileList.length === 0" class="empty-state">
                <p>No files uploaded yet</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-lg-6">
        <div class="card">
          <div class="card-body">
            <h4 class="card-title">Processing Status</h4>
            <div class="status-panel">
              <div class="progress-container" v-if="processing">
                <div class="progress">
                  <div 
                    class="progress-bar" 
                    :style="{ width: progressPercentage + '%' }"
                  ></div>
                </div>
                <p>{{ progressMessage }}</p>
              </div>
              
              <div class="results" v-if="processedCount > 0">
                <h5>Results</h5>
                <p>Processed: {{ processedCount }} | Failed: {{ failedCount }}</p>
                <p>Successfully stored in vector database</p>
              </div>
              
              <div class="status-info">
                <h5>System Status</h5>
                <ul>
                  <li><i class="fa fa-check-circle text-success"></i> Vector Database Connection: Active</li>
                  <li><i class="fa fa-check-circle text-success"></i> PDF Parser: Ready</li>
                  <li><i class="fa fa-check-circle text-success"></i> Embedding Engine: Ready</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
      this.$refs.fileInput.click();
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
    removeFile(index) {
      this.fileList.splice(index, 1);
    },
    processFiles() {
      if (this.fileList.length === 0) {
        alert('Please select at least one PDF file to process.');
        return;
      }

      this.processing = true;
      this.progressPercentage = 0;
      this.processedCount = 0;
      this.failedCount = 0;

      // 模拟处理过程
      this.simulateProcessing();
    },
    simulateProcessing() {
      // 更新每个文件的状态为正在处理
      this.fileList.forEach(file => {
        if (file.status === 'pending') {
          file.status = 'processing';
        }
      });

      let processed = 0;
      const total = this.fileList.length;
      
      const interval = setInterval(() => {
        if (processed < total) {
          // 随机成功或失败
          const isSuccess = Math.random() > 0.1; // 90% 成功率
          
          if (isSuccess) {
            this.fileList[processed].status = 'completed';
            this.processedCount++;
          } else {
            this.fileList[processed].status = 'failed';
            this.failedCount++;
          }
          
          processed++;
          this.progressPercentage = (processed / total) * 100;
          this.progressMessage = `Processing... ${processed}/${total}`;
        } else {
          clearInterval(interval);
          this.progressMessage = 'Processing completed!';
          this.processing = false;
          
          setTimeout(() => {
            this.progressMessage = 'Ready to process';
          }, 3000);
        }
      }, 800);
    },
    clearFiles() {
      this.fileList = [];
      this.processedCount = 0;
      this.failedCount = 0;
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
  border-radius: 4px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.1);
  margin-bottom: 25px;
}

.card-body {
  padding: 1.25rem;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #3498DB;
}

.upload-content i {
  font-size: 48px;
  color: #ccc;
  margin-bottom: 15px;
}

.upload-content h5 {
  margin-bottom: 10px;
}

.upload-actions {
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  margin-right: 10px;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background-color: #3498DB;
  color: white;
}

.btn-secondary {
  background-color: #95a5a6;
  color: white;
}

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