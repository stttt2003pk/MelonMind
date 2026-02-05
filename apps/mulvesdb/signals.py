from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import MulvesConnection, MulvesDataCache


@receiver(post_save, sender=MulvesConnection)
def clear_connection_cache(sender, instance, **kwargs):
    """当连接配置发生变化时清除相关缓存"""
    cache.delete(f'mulves_connection_{instance.id}')
    cache.delete('mulves_active_connections')


@receiver(post_delete, sender=MulvesConnection)
def clear_deleted_connection_cache(sender, instance, **kwargs):
    """当删除连接配置时清除相关缓存"""
    cache.delete(f'mulves_connection_{instance.id}')
    cache.delete('mulves_active_connections')


@receiver(post_save, sender=MulvesDataCache)
def clear_expired_cache(sender, instance, **kwargs):
    """定期清理过期缓存"""
    if instance.is_expired:
        instance.delete()


@receiver(post_delete, sender=MulvesDataCache)
def handle_cache_deletion(sender, instance, **kwargs):
    """处理缓存删除事件"""
    # 可以在这里添加额外的清理逻辑
    pass