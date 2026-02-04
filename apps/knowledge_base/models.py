from django.db import models
from django.contrib.auth.models import User


class KnowledgeEntry(models.Model):
    """Knowledge entry model"""
    CATEGORY_CHOICES = [
        ('network_device', 'Network Device'),
        ('troubleshooting', 'Troubleshooting'),
        ('best_practices', 'Best Practices'),
        ('configuration', 'Configuration Guide'),
        ('security', 'Security'),
    ]

    title = models.CharField(max_length=300, verbose_name='Title')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='Category')
    content = models.TextField(verbose_name='Content')
    tags = models.CharField(max_length=500, blank=True, verbose_name='Tags')
    source = models.CharField(max_length=200, blank=True, verbose_name='Source')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Created By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    is_published = models.BooleanField(default=True, verbose_name='Is Published')

    class Meta:
        verbose_name = 'Knowledge Entry'
        verbose_name_plural = 'Knowledge Entries'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class KnowledgeQueryLog(models.Model):
    """Knowledge query log"""
    query_text = models.TextField(verbose_name='Query Text')
    results_count = models.IntegerField(verbose_name='Results Count')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Query User')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Query Time')

    class Meta:
        verbose_name = 'Query Log'
        verbose_name_plural = 'Query Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.query_text[:50]}..."