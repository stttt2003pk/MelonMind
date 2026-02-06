# API 部署配置指南

## 开发环境配置

在开发环境中，我们使用 Vite 的代理功能来解决跨域问题：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Django 后端地址
      changeOrigin: true,
      secure: false,
    }
  }
}
```

### 工作原理
1. 前端运行在 `http://localhost:5173`
2. 发起 `/api/pdfloader/upload/` 请求
3. Vite 代理将请求转发到 `http://localhost:8000/api/pdfloader/upload/`
4. Django 后端处理请求并返回响应

## 生产环境配置方案

### 方案一：同源部署（推荐）

将前端和后端部署在同一域名下，使用 Nginx 进行反向代理：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 前端静态资源
    location / {
        root /path/to/your/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 请求转发到后端
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

在这种配置下，前端和后端都在 `https://yourdomain.com` 下，不会有跨域问题。

### 方案二：跨域部署

如果前端和后端必须部署在不同域名或端口上，需要在 Django 中配置 CORS：

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    # ...
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "https://frontend.yourdomain.com",
    "https://your-frontend-subdomain.vercel.app",  # 如果使用 Vercel 部署
]
```

同时在前端配置完整的后端地址：

```bash
# .env.production
VITE_API_BASE_URL=https://api.yourdomain.com
```

### 方案三：微服务架构

在微服务架构中，可以使用 API 网关统一管理所有服务：

```typescript
// 通过 API 网关统一访问
const getApiBaseUrl = () => {
  if (import.meta.env.MODE === 'production') {
    return import.meta.env.VITE_API_GATEWAY_URL || 'https://gateway.yourdomain.com';
  }
  return '/api';  // 开发环境仍使用代理
};
```

## 环境变量配置

### 开发环境 (.env.development)
```
VITE_API_BASE_URL=/api
```

### 测试环境 (.env.test)
```
VITE_API_BASE_URL=https://test-api.yourdomain.com
```

### 生产环境 (.env.production)
```
VITE_API_BASE_URL=/api
# 或者如果是跨域部署
# VITE_API_BASE_URL=https://api.yourdomain.com
```

## 部署最佳实践

### 1. 同源部署（推荐）
- 前后端部署在同一域名下，无跨域问题
- 安全性高，无需额外配置 CORS
- 性能好，减少跨域预检请求

### 2. 构建时配置
在构建时根据环境变量决定 API 地址：
```bash
# 构建生产版本
npm run build --mode production
```

### 3. 运行时配置
在某些情况下，也可以通过后端模板注入配置：
```html
<!-- 在 index.html 中 -->
<script>
  window.APP_CONFIG = {
    API_BASE_URL: "{{ api_base_url|default:'/api' }}"
  };
</script>
```

## 注意事项

1. **安全性**：不要在前端代码中硬编码敏感信息
2. **性能**：考虑使用 CDN 加速前端资源
3. **监控**：在生产环境中添加 API 请求监控和错误上报
4. **缓存**：合理配置 HTTP 缓存策略
5. **HTTPS**：生产环境中务必使用 HTTPS