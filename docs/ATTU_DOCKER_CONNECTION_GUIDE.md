# Attu Docker连接Milvus指南

## 📋 概述

本文档记录了如何正确配置和部署Attu（Milvus的Web管理界面）Docker容器，以成功连接到本地Milvus数据库。

## 🔧 问题背景

在本地开发环境中，直接使用 `localhost:19530` 作为Milvus连接地址会导致Attu容器无法连接，因为：
- Attu容器运行在Docker网络环境中
- `localhost` 对容器而言指向自身而非宿主机
- 不同容器间需要通过Docker网络进行通信

## 🎯 解决方案

### 方法一：使用自定义网络（推荐）

将Attu容器加入Milvus所在的Docker网络中。

#### 1. 检查现有容器网络

```bash
# 查看Milvus容器网络信息
docker inspect milvus-standalone | grep -A 15 Networks

# 查看Attu容器网络信息  
docker inspect attu | grep -A 15 Networks
```

#### 2. 停止并删除现有Attu容器

```bash
docker stop attu && docker rm attu
```

#### 3. 重新启动Attu并加入Milvus网络

```bash
docker run -d -p 8080:3000 \
  --network milvus \
  -e MILVUS_URL=milvus-standalone:19530 \
  --name attu \
  zilliz/attu:v2.6
```

#### 4. 验证连接

```bash
# 检查容器网络配置
docker inspect attu | grep -A 10 Networks

# 查看Attu日志
docker logs attu --tail 20

# 浏览器访问
http://localhost:8080
```

### 方法二：使用Milvus容器IP地址

如果不想改变网络配置，可以使用Milvus容器的实际IP地址。

#### 1. 获取Milvus容器IP

```bash
docker inspect milvus-standalone | grep IPAddress
```

#### 2. 启动Attu容器

```bash
docker run -d -p 8080:3000 \
  -e MILVUS_URL=172.19.0.4:19530 \
  --name attu \
  zilliz/attu:v2.6
```

## 📊 网络配置对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 自定义网络 | 稳定可靠，使用服务名 | 需要网络管理 | 生产环境推荐 |
| IP地址直连 | 配置简单 | IP可能变化 | 开发测试环境 |

## 🛠️ 常见问题排查

### 1. 连接失败错误日志
```
POST /api/v1/milvus/connect 401 Error: 14 UNAVAILABLE: No connection established
```

**原因：** 网络不通或地址配置错误

**解决方案：** 检查网络配置和连接地址

### 2. 端口冲突
```
docker: Error response from daemon: driver failed programming external connectivity on endpoint attu: Bind for 0.0.0.0:8080 failed: port is already allocated.
```

**解决方案：** 更换端口或停止占用端口的应用
```bash
docker run -d -p 8081:3000 --network milvus -e MILVUS_URL=milvus-standalone:19530 --name attu zilliz/attu:v2.6
```

### 3. 容器启动失败
```bash
docker logs attu  # 查看详细错误信息
```

## 🔍 验证步骤

### 1. 网络连通性测试
```bash
# 在Attu容器内测试Milvus连接
docker exec attu ping milvus-standalone

# 或者测试端口连通性
docker exec attu telnet milvus-standalone 19530
```

### 2. Milvus服务状态检查
```bash
# 检查Milvus容器健康状态
docker ps | grep milvus

# 测试Milvus API
curl http://localhost:19530/v1/vector/collections
```

## 📝 环境变量说明

| 环境变量 | 说明 | 示例值 |
|----------|------|--------|
| `MILVUS_URL` | Milvus服务地址 | `milvus-standalone:19530` |
| `PORT` | Attu服务端口 | `3000` (容器内) |

## 🚀 最佳实践

1. **使用服务名称而非IP**：提高稳定性和可维护性
2. **统一网络管理**：将相关服务放在同一网络中
3. **端口规划**：避免端口冲突，做好端口映射记录
4. **日志监控**：定期检查容器日志及时发现问题

## 📚 相关资源

- [Milvus官方文档](https://milvus.io/docs)
- [Attu GitHub仓库](https://github.com/zilliztech/attu)
- [Docker网络指南](https://docs.docker.com/network/)

---
*文档创建日期：2026-02-10*
*最后更新：2026-02-10*