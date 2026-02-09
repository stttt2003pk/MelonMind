<template>
  <div class="loading-overlay" v-if="isLoading">
    <div class="loading-content">
      <div class="loading-spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
      </div>
      
      <div class="loading-text">
        <h4>{{ title }}</h4>
        <p v-if="message">{{ message }}</p>
        
        <!-- 进度条 -->
        <div class="loading-progress" v-if="showProgress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: progress + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ Math.round(progress) }}%</span>
        </div>
        
        <!-- 文件处理进度 -->
        <div class="file-progress" v-if="currentFile">
          <p>正在处理: {{ currentFile }}</p>
          <div class="file-steps">
            <span 
              v-for="(step, index) in processingSteps" 
              :key="index"
              :class="['step', { active: currentStep >= index, completed: currentStep > index }]"
            >
              {{ step }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'LoadingOverlay',
  props: {
    isLoading: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '加载中...'
    },
    message: {
      type: String,
      default: ''
    },
    showProgress: {
      type: Boolean,
      default: false
    },
    progress: {
      type: Number,
      default: 0
    },
    currentFile: {
      type: String,
      default: ''
    },
    currentStep: {
      type: Number,
      default: 0
    }
  },
  setup() {
    const processingSteps = ref([
      '文件上传',
      '文本提取',
      '向量化处理',
      '存储到数据库'
    ]);

    return {
      processingSteps
    };
  }
};
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  backdrop-filter: blur(3px);
}

.loading-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
}

.loading-spinner {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-radius: 50%;
  animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
  border-top-color: #007bff;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
  border-top-color: #28a745;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
  border-top-color: #ffc107;
}

.spinner-ring:nth-child(4) {
  animation-delay: 0s;
  border-top-color: #dc3545;
}

@keyframes spinner-ring {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 20px;
  font-weight: 600;
}

.loading-text p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

/* 进度条样式 */
.loading-progress {
  margin: 20px 0;
}

.progress-bar {
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #28a745);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

/* 文件处理步骤 */
.file-progress {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.file-progress p {
  margin: 0 0 15px 0;
  font-weight: 500;
  color: #333;
}

.file-steps {
  display: flex;
  justify-content: space-between;
  position: relative;
}

.file-steps::before {
  content: '';
  position: absolute;
  top: 12px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #e9ecef;
  z-index: 1;
}

.step {
  position: relative;
  z-index: 2;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #666;
  font-weight: 500;
  transition: all 0.3s ease;
}

.step.active {
  background-color: #007bff;
  color: white;
  transform: scale(1.1);
}

.step.completed {
  background-color: #28a745;
  color: white;
}

.step:not(:first-child)::before {
  content: '';
  position: absolute;
  left: -30px;
  top: 11px;
  width: 30px;
  height: 2px;
  background-color: #e9ecef;
  transition: background-color 0.3s ease;
}

.step.completed:not(:first-child)::before {
  background-color: #28a745;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-content {
    padding: 20px;
    margin: 20px;
  }
  
  .loading-spinner {
    width: 60px;
    height: 60px;
  }
  
  .loading-text h4 {
    font-size: 18px;
  }
  
  .loading-text p {
    font-size: 13px;
  }
  
  .file-steps {
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
  }
  
  .step:not(:first-child)::before {
    display: none;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .loading-content {
    background: #2d2d2d;
    color: #fff;
  }
  
  .loading-text h4 {
    color: #fff;
  }
  
  .loading-text p {
    color: #ccc;
  }
  
  .progress-bar {
    background-color: #444;
  }
  
  .step {
    background-color: #444;
    color: #ccc;
  }
  
  .file-progress {
    border-top-color: #444;
  }
}
</style>