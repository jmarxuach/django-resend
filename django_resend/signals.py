"""
Django signals for django-resend package.

These signals allow consuming applications to hook into webhook events
without tight coupling.
"""
from django.dispatch import Signal

# Signal sent when a webhook event is received and stored
webhook_event_received = Signal()

# Signal sent when an event is successfully processed
webhook_event_processed = Signal()

# Signal sent when event processing fails
webhook_event_failed = Signal()
