from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import KnowledgeEntry, KnowledgeQueryLog


@receiver(pre_save, sender=KnowledgeEntry)
def knowledge_entry_pre_save(sender, instance, **kwargs):
    """Signal handler before KnowledgeEntry save"""
    # Could add validation, auto-tagging, content processing, etc.
    if not instance.tags and instance.category:
        # Auto-generate tags based on category
        instance.tags = instance.category.replace('_', ' ')


@receiver(post_save, sender=KnowledgeEntry)
def knowledge_entry_post_save(sender, instance, created, **kwargs):
    """Signal handler after KnowledgeEntry save"""
    if created:
        # Log creation event, send notifications, update search index, etc.
        pass
    else:
        # Handle updates - could update search index, send notifications, etc.
        pass


@receiver(post_save, sender=KnowledgeQueryLog)
def knowledge_query_log_post_save(sender, instance, created, **kwargs):
    """Signal handler after KnowledgeQueryLog save"""
    if created:
        # Could trigger analytics, user behavior tracking, etc.
        pass