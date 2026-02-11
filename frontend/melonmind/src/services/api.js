import axios from 'axios';

// 根据环境决定API基础URL
const getApiBaseUrl = () => {
  if (import.meta.env.MODE === 'production') {
    // 生产环境：使用相对路径或从环境变量获取
    return import.meta.env.VITE_API_BASE_URL || '/api';
  } else {
    // 开发环境：使用相对路径，会被vite代理转发
    return '/api';
  }
};

// 创建axios实例
const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 60000, // 增加超时时间以适应大文件上传
  headers: {
    'Content-Type': 'application/json',
  },
  // 允许携带凭证
  withCredentials: true
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // 添加请求时间戳用于调试
    config.metadata = { startTime: new Date().getTime() };
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 记录响应时间
    const endTime = new Date().getTime();
    const duration = endTime - (response.config.metadata?.startTime || endTime);
    console.log(`API Response: ${response.config.url} (${duration}ms)`);
    return response;
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error);
    
    // 处理不同类型的错误
    if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
      error.userMessage = '网络连接失败，请检查网络设置或稍后重试';
    } else if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status;
      switch (status) {
        case 400:
          error.userMessage = error.response.data?.detail || '请求参数错误';
          break;
        case 401:
          error.userMessage = '未授权访问，请重新登录';
          localStorage.removeItem('authToken');
          break;
        case 403:
          error.userMessage = '权限不足，无法执行此操作';
          break;
        case 404:
          error.userMessage = '请求的资源不存在';
          break;
        case 413:
          error.userMessage = '文件过大，请选择较小的文件';
          break;
        case 422:
          error.userMessage = '文件格式不支持或已存在相同文件';
          break;
        case 500:
          error.userMessage = '服务器内部错误，请稍后重试';
          break;
        case 502:
        case 503:
        case 504:
          error.userMessage = '服务暂时不可用，请稍后重试';
          break;
        default:
          error.userMessage = `请求失败 (${status})`;
      }
    } else if (error.request) {
      // 请求发出但没有收到响应
      error.userMessage = '服务器无响应，请检查网络连接';
    } else {
      // 其他错误
      error.userMessage = '请求配置错误';
    }
    
    return Promise.reject(error);
  }
);

// 添加一个辅助函数用于动态更改baseURL
apiClient.setBaseURL = (newBaseURL) => {
  apiClient.defaults.baseURL = newBaseURL;
};

// 文件上传专用配置
const createUploadClient = () => {
  return axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 300000, // 5分钟超时
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    withCredentials: false,
    // 上传进度回调
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      // 这里可以触发全局事件或store更新
      window.dispatchEvent(new CustomEvent('uploadProgress', {
        detail: { progress: percentCompleted }
      }));
    }
  });
};

// PDF文档处理相关API
const pdfLoaderAPI = {
  // 上传PDF文件（带进度跟踪）
  uploadPDF: async (formData, onProgress) => {
    const uploadClient = createUploadClient();
    
    if (onProgress) {
      uploadClient.defaults.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      };
    }
    
    try {
      const response = await uploadClient.post('/pdfloader/upload/', formData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 批量上传PDF文件
  batchUploadPDF: async (files, options = {}, onProgress) => {
    const results = [];
    const totalFiles = files.length;
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);
      formData.append('milvus_connection_id', options.milvusConnectionId || 1);
      formData.append('collection_name', options.collectionName || `pdf_docs_${Date.now()}`);
      
      try {
        // 单个文件进度回调
        const singleProgress = onProgress ? (percent) => {
          const overallProgress = Math.round(((i * 100) + percent) / totalFiles);
          onProgress(overallProgress, i, file.name);
        } : null;
        
        const result = await pdfLoaderAPI.uploadPDF(formData, singleProgress);
        results.push({ success: true, file: file.name, data: result });
      } catch (error) {
        results.push({ 
          success: false, 
          file: file.name, 
          error: error.userMessage || error.message 
        });
      }
    }
    
    return results;
  },
  
  // 获取PDF文档列表
  getDocuments: async (params = {}) => {
    try {
      const response = await apiClient.get('/pdfloader/documents/', { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取PDF文档详情
  getDocumentDetail: async (documentId) => {
    try {
      const response = await apiClient.get(`/pdfloader/documents/${documentId}/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取PDF文档分块信息
  getDocumentChunks: async (documentId) => {
    try {
      const response = await apiClient.get(`/pdfloader/documents/${documentId}/chunks/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取处理状态
  getProcessingStatus: async (documentId) => {
    try {
      const response = await apiClient.get(`/pdfloader/documents/${documentId}/status/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 向量搜索
  vectorSearch: async (searchData) => {
    try {
      const response = await apiClient.post('/pdfloader/search/', searchData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取集合信息
  getCollectionInfo: async (collectionName) => {
    try {
      const response = await apiClient.get(`/pdfloader/collections/${collectionName}/info/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 删除文档
  deleteDocument: async (documentId) => {
    try {
      const response = await apiClient.delete(`/pdfloader/documents/${documentId}/`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取上传历史记录
  getUploadHistory: async (limit = 50) => {
    try {
      const response = await apiClient.get('/pdfloader/history/', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

// 知识库相关API
const knowledgeBaseAPI = {
  // 获取文档统计信息
  getDocumentStats: async () => {
    try {
      const response = await apiClient.get('/knowledge/document-stats/');
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取系统健康状态
  getSystemHealth: async () => {
    try {
      const response = await apiClient.get('/knowledge/system-health/');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

// 通用API工具函数
const apiUtils = {
  // 检查API连通性
  checkConnectivity: async () => {
    try {
      await apiClient.get('/health/');
      return { connected: true };
    } catch (error) {
      return { 
        connected: false, 
        error: error.userMessage || '无法连接到服务器' 
      };
    }
  },
  
  // 取消请求
  cancelRequest: (cancelToken) => {
    if (cancelToken) {
      cancelToken.cancel('Operation canceled by the user.');
    }
  }
};

export default apiClient;
export { knowledgeBaseAPI, pdfLoaderAPI };