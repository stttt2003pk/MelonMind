import axios from 'axios';

// 根据环境决定API基础URL
const getApiBaseUrl = () => {
  if (import.meta.env.MODE === 'production') {
    // 生产环境：使用相对路径或从环境变量获取
    // 如果前端和后端部署在同一域名下，使用相对路径
    return import.meta.env.VITE_API_BASE_URL || '/api';
  } else {
    // 开发环境：使用相对路径，会被vite代理转发
    return '/api';
  }
};

// 创建axios实例
const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么，比如添加认证token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    return response;
  },
  (error) => {
    // 对响应错误做点什么
    console.error('API Error:', error);
    
    // 特殊处理网络错误或CORS错误
    if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
      console.error('Network error - check if backend is running and accessible');
    }
    
    return Promise.reject(error);
  }
);

// 添加一个辅助函数用于动态更改baseURL（适用于多环境切换）
apiClient.setBaseURL = (newBaseURL) => {
  apiClient.defaults.baseURL = newBaseURL;
};

// 知识库相关API
const knowledgeBaseAPI = {
  // 获取文档统计信息
  getDocumentStats: () => {
    return apiClient.get('/knowledge/document-stats/');
  }
};

export default apiClient;
export { knowledgeBaseAPI };