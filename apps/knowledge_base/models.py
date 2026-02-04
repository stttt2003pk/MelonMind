from django.db import models
from django.contrib.auth.models import User


class KnowledgeEntry(models.Model):
    """知识条目模型"""
    CATEGORY_CHOICES = [
        ('network_device', '网络设备'),
        ('troubleshooting', '故障排除'),
        ('best_practices', '最佳实践'),
        ('configuration', '配置指南'),
        ('security', '安全'),
    ]

    title = models.CharField(max_length=300, verbose_name='标题')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='分类')
    content = models.TextField(verbose_name='内容')
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签')
    source = models.CharField(max_length=200, blank=True, verbose_name='来源')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_published = models.BooleanField(default=True, verbose_name='是否发布')

    class Meta:
        verbose_name = '知识条目'
        verbose_name_plural = '知识条目'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class KnowledgeQueryLog(models.Model):
    """知识查询日志"""
    query_text = models.TextField(verbose_name='查询文本')
    results_count = models.IntegerField(verbose_name='结果数量')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='查询用户')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='查询时间')

    class Meta:
        verbose_name = '查询日志'
        verbose_name_plural = '查询日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.query_text[:50]}..."