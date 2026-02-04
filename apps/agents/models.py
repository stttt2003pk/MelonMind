from django.db import models
from django.contrib.auth.models import User


class AgentFlow(models.Model):
    """Agent flow model"""
    name = models.CharField(max_length=200, verbose_name='Flow Name')
    description = models.TextField(verbose_name='Description', blank=True)
    flow_config = models.JSONField(verbose_name='Flow Configuration')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Created By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    is_active = models.BooleanField(default=True, verbose_name='Is Active')

    class Meta:
        verbose_name = 'Agent Flow'
        verbose_name_plural = 'Agent Flows'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class AgentExecution(models.Model):
    """Agent execution record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    flow = models.ForeignKey(AgentFlow, on_delete=models.CASCADE, verbose_name='Associated Flow')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    input_data = models.JSONField(verbose_name='Input Data')
    output_data = models.JSONField(null=True, blank=True, verbose_name='Output Data')
    error_message = models.TextField(blank=True, verbose_name='Error Message')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Start Time')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completion Time')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Agent Execution Record'
        verbose_name_plural = 'Agent Execution Records'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.flow.name} - {self.get_status_display()}"