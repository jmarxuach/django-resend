from django.db import models
from django.utils import timezone
import json


class ResendWebhookEvent(models.Model):
    """
    Model to store Resend webhook events.
    
    Stores all webhook event data from Resend and provides a status field
    for asynchronous processing by the consuming application.
    """
    
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_PROCESSED = 'processed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_PROCESSED, 'Processed'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Resend event identification
    event_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='Unique identifier for the event from Resend'
    )
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Type of event (e.g., email.sent, email.delivered, email.bounced)'
    )
    
    # Timestamp from Resend
    timestamp = models.DateTimeField(
        help_text='Timestamp when the event occurred (from Resend)'
    )
    
    # Email-related fields (common across most events)
    email = models.EmailField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Email address associated with the event'
    )
    message_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text='Resend message ID'
    )
    
    # Raw payload - stores complete event data as JSON
    payload = models.JSONField(
        default=dict,
        help_text='Complete webhook payload from Resend'
    )
    
    # Processing status for async handling
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text='Processing status for asynchronous handling'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When the event was received and stored'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the event was successfully processed'
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text='Error message if processing failed'
    )
    retry_count = models.IntegerField(
        default=0,
        help_text='Number of processing attempts'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['event_type', 'status']),
        ]
        verbose_name = 'Resend Webhook Event'
        verbose_name_plural = 'Resend Webhook Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.event_id} ({self.status})"
    
    def mark_processing(self):
        """Mark event as being processed."""
        self.status = self.STATUS_PROCESSING
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_processed(self):
        """Mark event as successfully processed."""
        self.status = self.STATUS_PROCESSED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at', 'updated_at'])
    
    def mark_failed(self, error_message=''):
        """Mark event as failed with error message."""
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])
    
    def get_payload_data(self):
        """Get the 'data' field from the payload."""
        return self.payload.get('data', {})
    
    def get_payload_type(self):
        """Get the event type from payload."""
        return self.payload.get('type', '')
