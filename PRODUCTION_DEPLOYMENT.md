# 生产环境部署指南

## CORS 配置最佳实践

### 1. 同源部署（推荐方案）

将前端和后端部署在同一域名下，通过反向代理（如Nginx）分发请求：

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

在这种配置下，前端和后端都在 `https://yourdomain.com` 下，不会有跨域问题，CORS配置可以保持最小化。

### 2. 跨域部署（备选方案）

如果前端和后端必须部署在不同域名或端口上，需要在 `.env` 文件中明确配置：

```bash
# .env.production
CORS_ALLOWED_ORIGINS=https://frontend.yourdomain.com,https://admin.yourdomain.com
```

### 3. 环境变量配置

在生产环境中，通过环境变量控制CORS设置：

- `CORS_ALLOWED_ORIGINS`: 允许的来源列表，逗号分隔
- `CORS_ALLOW_ALL_ORIGINS`: 是否允许所有来源（调试用，生产环境不推荐）

### 4. 安全注意事项

1. **永远不要在生产环境中启用** `CORS_ALLOW_ALL_ORIGINS=true`
2. **明确列出所有合法的前端域名**，不要使用通配符 `*`
3. **定期审查**允许的来源列表
4. **使用HTTPS**在生产环境中

### 5. 示例配置

#### 开发环境 (.env)
```bash
DEBUG=true
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### 生产环境 (.env)
```bash
DEBUG=false
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_ALL_ORIGINS=false
```

### 6. 部署验证步骤

部署后验证CORS配置：

1. 检查API端点是否正常响应
2. 确认前端可以正常调用API
3. 验证非授权来源的请求被拒绝
4. 测试HTTPS重定向（如适用）

## 部署检查清单

- [ ] 环境变量已正确配置
- [ ] 数据库连接正常
- [ ] 静态文件已收集
- [ ] CORS设置已根据部署架构配置
- [ ] 日志配置已设置
- [ ] 安全设置已调整为生产模式