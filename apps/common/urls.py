# -*- coding: utf-8 -*-
# Common app URL configuration file
# Contains routing configuration for public interfaces like homepage and health check

from django.urls import path
from . import views

# URL pattern configuration
# Defines all routing rules for the common application
urlpatterns = [
    # HTML主页路由 - 用户直接访问的友好界面
    path('', views.home_page, name='home_page'),
    # API首页路由 - 返回JSON格式的系统信息
    path('api/', views.api_home, name='api_home'),
    # 健康检查路由 - 无需认证即可访问
    path('health/', views.health_check, name='health_check'),
]