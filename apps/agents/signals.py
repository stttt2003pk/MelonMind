from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import AgentFlow, AgentExecution


@receiver(pre_save, sender=AgentExecution)
def agent_execution_pre_save(sender, instance, **kwargs):
    """Signal handler before AgentExecution save"""
    # Set start time when status changes to running
    if instance.status == 'running' and instance.started_at is None:
        instance.started_at = timezone.now()
    
    # Set completion time when status changes to final state
    if instance.status in ['completed', 'failed', 'cancelled'] and instance.completed_at is None:
        instance.completed_at = timezone.now()


@receiver(post_save, sender=AgentFlow)
def agent_flow_post_save(sender, instance, created, **kwargs):
    """Signal handler after AgentFlow save"""
    if created:
        # Log or perform actions when new flow is created
        pass
    else:
        # Log or perform actions when flow is updated
        pass


@receiver(post_save, sender=AgentExecution)
def agent_execution_post_save(sender, instance, created, **kwargs):
    """Signal handler after AgentExecution save"""
    if created:
        # Log or perform actions when new execution is created
        pass
    else:
        # Log or perform actions when execution is updated
        # Could trigger notifications, update statistics, etc.
        pass