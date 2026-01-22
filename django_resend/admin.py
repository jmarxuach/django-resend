from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ResendWebhookEvent


@admin.register(ResendWebhookEvent)
class ResendWebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_id_short',
        'event_type',
        'email',
        'status_badge',
        'created_at',
        'processed_at',
        'retry_count',
    ]
    list_filter = [
        'status',
        'event_type',
        'created_at',
    ]
    search_fields = [
        'event_id',
        'email',
        'message_id',
        'event_type',
    ]
    readonly_fields = [
        'event_id',
        'event_type',
        'timestamp',
        'email',
        'message_id',
        'payload_display',
        'created_at',
        'updated_at',
        'processed_at',
        'retry_count',
    ]
    fieldsets = (
        ('Event Information', {
            'fields': ('event_id', 'event_type', 'timestamp')
        }),
        ('Email Information', {
            'fields': ('email', 'message_id')
        }),
        ('Status', {
            'fields': ('status', 'retry_count', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
        ('Payload', {
            'fields': ('payload_display',),
            'classes': ('collapse',)
        }),
    )
    
    def event_id_short(self, obj):
        """Display shortened event ID."""
        if len(obj.event_id) > 20:
            return f"{obj.event_id[:20]}..."
        return obj.event_id
    event_id_short.short_description = 'Event ID'
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            ResendWebhookEvent.STATUS_PENDING: '#ffc107',
            ResendWebhookEvent.STATUS_PROCESSING: '#17a2b8',
            ResendWebhookEvent.STATUS_PROCESSED: '#28a745',
            ResendWebhookEvent.STATUS_FAILED: '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payload_display(self, obj):
        """Display formatted JSON payload."""
        import json
        formatted_json = json.dumps(obj.payload, indent=2)
        return format_html('<pre style="max-height: 400px; overflow: auto;">{}</pre>', formatted_json)
    payload_display.short_description = 'Payload (JSON)'
    
    def has_add_permission(self, request):
        """Disable manual addition of events."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow changing status and error_message only."""
        return True
    
    actions = ['mark_as_pending', 'mark_as_processed', 'mark_as_failed']
    
    def mark_as_pending(self, request, queryset):
        """Mark selected events as pending."""
        queryset.update(status=ResendWebhookEvent.STATUS_PENDING)
        self.message_user(request, f"{queryset.count()} events marked as pending.")
    mark_as_pending.short_description = "Mark selected as pending"
    
    def mark_as_processed(self, request, queryset):
        """Mark selected events as processed."""
        queryset.update(
            status=ResendWebhookEvent.STATUS_PROCESSED,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{queryset.count()} events marked as processed.")
    mark_as_processed.short_description = "Mark selected as processed"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected events as failed."""
        queryset.update(status=ResendWebhookEvent.STATUS_FAILED)
        self.message_user(request, f"{queryset.count()} events marked as failed.")
    mark_as_failed.short_description = "Mark selected as failed"
