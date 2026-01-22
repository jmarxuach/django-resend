"""
Utility functions for processing Resend webhook events asynchronously.
"""
import logging
from django.utils import timezone
from .models import ResendWebhookEvent
from .signals import webhook_event_processed, webhook_event_failed

logger = logging.getLogger(__name__)


def get_pending_events(limit=None, event_type=None):
    """
    Get pending webhook events ready for processing.
    
    Args:
        limit (int, optional): Maximum number of events to return
        event_type (str, optional): Filter by event type
        
    Returns:
        QuerySet: QuerySet of ResendWebhookEvent objects
    """
    queryset = ResendWebhookEvent.objects.filter(
        status=ResendWebhookEvent.STATUS_PENDING
    )
    
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    
    queryset = queryset.order_by('created_at')
    
    if limit:
        queryset = queryset[:limit]
    
    return queryset


def process_event(event, handler=None):
    """
    Process a single webhook event.
    
    Args:
        event (ResendWebhookEvent): The event to process
        handler (callable, optional): Custom handler function
        
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    if event.status != ResendWebhookEvent.STATUS_PENDING:
        logger.warning(f"Event {event.event_id} is not pending, skipping")
        return False
    
    try:
        event.mark_processing()
        
        # If custom handler provided, use it
        if handler:
            handler(event)
        else:
            # Default: just mark as processed
            # Consuming apps should connect to signals or provide handlers
            pass
        
        event.mark_processed()
        webhook_event_processed.send(
            sender=ResendWebhookEvent,
            event=event
        )
        
        logger.info(f"Successfully processed event {event.event_id}")
        return True
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing event {event.event_id}: {error_message}")
        event.mark_failed(error_message)
        webhook_event_failed.send(
            sender=ResendWebhookEvent,
            event=event,
            error=e
        )
        return False


def process_pending_events(limit=None, event_type=None, handler=None):
    """
    Process multiple pending events.
    
    Args:
        limit (int, optional): Maximum number of events to process
        event_type (str, optional): Filter by event type
        handler (callable, optional): Custom handler function
        
    Returns:
        dict: Statistics about processing
    """
    events = get_pending_events(limit=limit, event_type=event_type)
    
    stats = {
        'total': 0,
        'processed': 0,
        'failed': 0,
    }
    
    for event in events:
        stats['total'] += 1
        if process_event(event, handler=handler):
            stats['processed'] += 1
        else:
            stats['failed'] += 1
    
    logger.info(
        f"Processed {stats['processed']}/{stats['total']} events "
        f"({stats['failed']} failed)"
    )
    
    return stats


def retry_failed_events(limit=None, max_retries=3):
    """
    Retry failed events that haven't exceeded max retries.
    
    Args:
        limit (int, optional): Maximum number of events to retry
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        dict: Statistics about retry processing
    """
    queryset = ResendWebhookEvent.objects.filter(
        status=ResendWebhookEvent.STATUS_FAILED,
        retry_count__lt=max_retries
    ).order_by('created_at')
    
    if limit:
        queryset = queryset[:limit]
    
    # Reset status to pending for retry
    queryset.update(status=ResendWebhookEvent.STATUS_PENDING)
    
    stats = {
        'total': queryset.count(),
        'processed': 0,
        'failed': 0,
    }
    
    for event in queryset:
        if process_event(event):
            stats['processed'] += 1
        else:
            stats['failed'] += 1
    
    return stats
