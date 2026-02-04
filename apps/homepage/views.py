from django.shortcuts import render
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

def home_page(request):
    """
    Main homepage view - serves the MelonMind welcome page
    """
    logger.info("Homepage accessed")
    context = {
        'title': 'MelonMind - 智能运维助手',
        'version': '1.0.0',
        'features': [
            {
                'name': '智能代理',
                'description': '基于LangChain和LangGraph的强大AI代理系统'
            },
            {
                'name': '知识库',
                'description': '集成Mulves连接器的网络运维知识库'
            },
            {
                'name': '实时监控',
                'description': '实时监控系统状态和性能指标'
            }
        ]
    }
    return render(request, 'homepage/home.html', context)

def health_check(request):
    """
    Simple health check endpoint for the homepage app
    """
    return HttpResponse("Homepage service is running", content_type="text/plain")