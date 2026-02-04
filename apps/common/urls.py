# -*- coding: utf-8 -*-
# Common app URL configuration file
# Contains routing configuration for public interfaces like homepage and health check

from django.urls import path
from . import views

# URL pattern configuration
# Defines all routing rules for the common application
urlpatterns = [
    # Homepage route - returns basic API information
    path('', views.home, name='home'),
    # Health check route - accessible without authentication
    path('health/', views.health_check, name='health_check'),
]