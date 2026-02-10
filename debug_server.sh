#!/bin/bash

# MelonMind Debug Server 启动脚本

echo "=== MelonMind Debug Server 启动脚本 ==="

# 检查端口占用
echo "检查8000端口占用情况..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "发现8000端口被占用，正在终止相关进程..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# 检查Poetry环境
echo "检查Poetry环境..."
if ! command -v poetry &> /dev/null; then
    echo "错误: 未找到poetry命令"
    exit 1
fi

# 显示环境信息
echo "当前工作目录: $(pwd)"
echo "Python环境路径: $(poetry run which python)"
echo "Django版本: $(poetry run python -c "import django; print(django.get_version())")"

# 启动Django开发服务器
echo "启动Django开发服务器..."
echo "访问地址: http://localhost:8000"
echo "管理后台: http://localhost:8000/admin/"
echo "按 Ctrl+C 停止服务器"
echo ""

# 使用Poetry运行服务器
poetry run python manage.py runserver
