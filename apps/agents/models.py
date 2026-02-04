from django.db import models
from django.contrib.auth.models import User


class AgentFlow(models.Model):
    """Agent 流程模型"""
    name = models.CharField(max_length=200, verbose_name='流程名称')
    description = models.TextField(verbose_name='描述', blank=True)
    flow_config = models.JSONField(verbose_name='流程配置')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    class Meta:
        verbose_name = 'Agent 流程'
        verbose_name_plural = 'Agent 流程'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class AgentExecution(models.Model):
    """Agent 执行记录"""
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    flow = models.ForeignKey(AgentFlow, on_delete=models.CASCADE, verbose_name='关联流程')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    input_data = models.JSONField(verbose_name='输入数据')
    output_data = models.JSONField(null=True, blank=True, verbose_name='输出数据')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'Agent 执行记录'
        verbose_name_plural = 'Agent 执行记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.flow.name} - {self.get_status_display()}"