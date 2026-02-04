# -*- coding: utf-8 -*-
# Homepage app URL configuration
# Contains routing for the main website homepage

from django.urls import path
from . import views

urlpatterns = [
    # Main homepage route
    path('', views.home_page, name='home_page'),
    # Health check for homepage service
    path('health/', views.health_check, name='homepage_health'),
]