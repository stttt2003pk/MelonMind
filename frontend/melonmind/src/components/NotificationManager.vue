<template>
  <div class="notification-container">
    <transition-group name="notification" tag="div">
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        :class="['notification', `notification-${notification.type}`]"
        @mouseenter="pauseTimer(notification)"
        @mouseleave="resumeTimer(notification)"
      >
        <div class="notification-content">
          <div class="notification-icon">
            <i :class="getIconClass(notification.type)"></i>
          </div>
          <div class="notification-body">
            <h6 class="notification-title" v-if="notification.title">
              {{ notification.title }}
            </h6>
            <p class="notification-message">{{ notification.message }}</p>
          </div>
          <button 
            class="notification-close" 
            @click="removeNotification(notification.id)"
          >
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <!-- 进度条 -->
        <div 
          v-if="notification.duration > 0" 
          class="notification-progress"
          :style="{ width: `${notification.progress}%` }"
        ></div>
      </div>
    </transition-group>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';

export default {
  name: 'NotificationManager',
  setup() {
    const notifications = ref([]);
    let notificationId = 0;

    // 获取图标类名
    const getIconClass = (type) => {
      const icons = {
        success: 'fa fa-check-circle',
        error: 'fa fa-exclamation-circle',
        warning: 'fa fa-exclamation-triangle',
        info: 'fa fa-info-circle'
      };
      return icons[type] || icons.info;
    };

    // 添加通知
    const addNotification = (options) => {
      const id = ++notificationId;
      const notification = {
        id,
        title: options.title || '',
        message: options.message || '',
        type: options.type || 'info', // success, error, warning, info
        duration: options.duration !== undefined ? options.duration : 5000, // 0表示永久显示
        closable: options.closable !== undefined ? options.closable : true,
        progress: 100,
        timer: null
      };

      notifications.value.push(notification);

      // 自动关闭定时器
      if (notification.duration > 0) {
        startTimer(notification);
      }

      return id;
    };

    // 开始计时器
    const startTimer = (notification) => {
      if (notification.duration <= 0) return;

      const interval = 50; // 50ms更新一次
      const decrement = (interval / notification.duration) * 100;
      
      notification.timer = setInterval(() => {
        if (!notification.paused) {
          notification.progress -= decrement;
          
          if (notification.progress <= 0) {
            removeNotification(notification.id);
          }
        }
      }, interval);
    };

    // 暂停计时器
    const pauseTimer = (notification) => {
      notification.paused = true;
    };

    // 恢复计时器
    const resumeTimer = (notification) => {
      notification.paused = false;
    };

    // 移除通知
    const removeNotification = (id) => {
      const index = notifications.value.findIndex(n => n.id === id);
      if (index !== -1) {
        const notification = notifications.value[index];
        
        // 清除定时器
        if (notification.timer) {
          clearInterval(notification.timer);
        }
        
        // 添加移除动画延迟
        setTimeout(() => {
          notifications.value.splice(index, 1);
        }, 300);
      }
    };

    // 清除所有通知
    const clearAll = () => {
      notifications.value.forEach(notification => {
        if (notification.timer) {
          clearInterval(notification.timer);
        }
      });
      notifications.value = [];
    };

    // 快捷方法
    const success = (message, title = '', options = {}) => {
      return addNotification({
        ...options,
        title,
        message,
        type: 'success'
      });
    };

    const error = (message, title = '', options = {}) => {
      return addNotification({
        ...options,
        title,
        message,
        type: 'error',
        duration: options.duration || 0 // 错误消息默认不自动关闭
      });
    };

    const warning = (message, title = '', options = {}) => {
      return addNotification({
        ...options,
        title,
        message,
        type: 'warning'
      });
    };

    const info = (message, title = '', options = {}) => {
      return addNotification({
        ...options,
        title,
        message,
        type: 'info'
      });
    };

    // 全局事件监听
    const handleGlobalNotification = (event) => {
      const { type, message, title, options } = event.detail;
      switch (type) {
        case 'success':
          success(message, title, options);
          break;
        case 'error':
          error(message, title, options);
          break;
        case 'warning':
          warning(message, title, options);
          break;
        case 'info':
          info(message, title, options);
          break;
      }
    };

    onMounted(() => {
      // 监听全局通知事件
      window.addEventListener('showNotification', handleGlobalNotification);
    });

    onUnmounted(() => {
      // 清理事件监听器
      window.removeEventListener('showNotification', handleGlobalNotification);
      clearAll();
    });

    return {
      notifications,
      getIconClass,
      removeNotification,
      pauseTimer,
      resumeTimer
    };
  }
};

// 全局通知方法
export const notify = {
  success(message, title = '', options = {}) {
    window.dispatchEvent(new CustomEvent('showNotification', {
      detail: { type: 'success', message, title, options }
    }));
  },
  
  error(message, title = '', options = {}) {
    window.dispatchEvent(new CustomEvent('showNotification', {
      detail: { type: 'error', message, title, options }
    }));
  },
  
  warning(message, title = '', options = {}) {
    window.dispatchEvent(new CustomEvent('showNotification', {
      detail: { type: 'warning', message, title, options }
    }));
  },
  
  info(message, title = '', options = {}) {
    window.dispatchEvent(new CustomEvent('showNotification', {
      detail: { type: 'info', message, title, options }
    }));
  }
};
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  width: 350px;
  max-width: calc(100vw - 40px);
}

.notification {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin-bottom: 15px;
  overflow: hidden;
  border-left: 4px solid #ddd;
  transform-origin: top right;
  transition: all 0.3s ease;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.8);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.8);
}

.notification-content {
  display: flex;
  align-items: flex-start;
  padding: 15px;
}

.notification-icon {
  margin-right: 12px;
  font-size: 20px;
  align-self: flex-start;
}

.notification-success .notification-icon {
  color: #28a745;
}

.notification-error .notification-icon {
  color: #dc3545;
}

.notification-warning .notification-icon {
  color: #ffc107;
}

.notification-info .notification-icon {
  color: #17a2b8;
}

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-title {
  margin: 0 0 5px 0;
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.notification-message {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  word-break: break-word;
}

.notification-close {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 10px;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.notification-close:hover {
  background: #f0f0f0;
  color: #666;
}

.notification-progress {
  height: 3px;
  background: linear-gradient(90deg, #007bff, #0056b3);
  transition: width 0.05s linear;
}

/* 不同类型的通知样式 */
.notification-success {
  border-left-color: #28a745;
}

.notification-error {
  border-left-color: #dc3545;
}

.notification-warning {
  border-left-color: #ffc107;
}

.notification-info {
  border-left-color: #17a2b8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notification-container {
    top: 10px;
    right: 10px;
    left: 10px;
    width: auto;
  }
  
  .notification {
    margin-bottom: 10px;
  }
  
  .notification-content {
    padding: 12px;
  }
  
  .notification-icon {
    font-size: 18px;
    margin-right: 10px;
  }
  
  .notification-title {
    font-size: 13px;
  }
  
  .notification-message {
    font-size: 12px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .notification {
    background: #2d2d2d;
    color: #fff;
  }
  
  .notification-title {
    color: #fff;
  }
  
  .notification-message {
    color: #ccc;
  }
  
  .notification-close {
    color: #999;
  }
  
  .notification-close:hover {
    background: #444;
    color: #fff;
  }
}
</style>