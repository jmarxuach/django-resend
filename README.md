# django-resend

A Django package for handling Resend email webhooks with asynchronous event processing.

## About

**Important**: This package is designed to handle Resend webhook events, not to send emails. To send emails, you must use the official [Resend Python library](https://github.com/resend/resend-python):

```bash
pip install resend
```

```python
import resend

resend.api_key = "re_your_api_key"
resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": "delivered@resend.dev",
    "subject": "Hello World",
    "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
})
```

This package (`django-resend`) is specifically useful for **handling large amounts of Resend webhook events** efficiently. It stores webhook events in your database with a status field, allowing you to process them asynchronously and avoid webhook timeout issues when dealing with high volumes of events.

## Features

- **Webhook Event Storage**: Automatically stores all Resend webhook events in the database
- **Asynchronous Processing**: Events are stored with a status field for async processing
- **Status Tracking**: Track event processing status (pending, processing, processed, failed)
- **Django Admin Integration**: Built-in admin interface for managing events
- **Signal Support**: Django signals for hooking into event processing
- **Idempotency**: Prevents duplicate event processing

## Installation

```bash
pip install django-resend
```

## Configuration

Add `django_resend` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'django_resend',
]
```

Add the Resend API key to your settings:

```python
RESEND_APIKEY = 're_your_api_key_here'
```

Optional settings:

```python
# Webhook signing secret for validation (if using Resend webhook signing)
RESEND_WEBHOOK_SECRET = 'whsec_your_secret'

# Webhook timeout in seconds (default: 30)
RESEND_WEBHOOK_TIMEOUT = 30
```

Run migrations:

```bash
python manage.py migrate
```

## URL Configuration

Include the django-resend URLs in your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('resend/', include('django_resend.urls')),
]
```

This will create a webhook endpoint at `/resend/webhook/` that Resend can POST to.

## Usage

### Webhook Setup

1. Configure your Resend webhook URL to point to: `https://yourdomain.com/resend/webhook/`
2. Resend will POST events to this endpoint
3. Events are automatically stored in the database with `pending` status

### Processing Events

#### Option 1: Using Signals

Connect to signals in your app:

```python
from django.dispatch import receiver
from django_resend.signals import webhook_event_received, webhook_event_processed

@receiver(webhook_event_received)
def handle_resend_event(sender, event, payload, **kwargs):
    """Handle when a webhook event is received."""
    print(f"Received event: {event.event_type} - {event.event_id}")

@receiver(webhook_event_processed)
def on_event_processed(sender, event, **kwargs):
    """Handle when an event is successfully processed."""
    print(f"Processed event: {event.event_id}")
```

#### Option 2: Using Utility Functions

Process events programmatically:

```python
from django_resend.utils import process_pending_events, process_event
from django_resend.models import ResendWebhookEvent

# Process all pending events
stats = process_pending_events()
print(f"Processed {stats['processed']}/{stats['total']} events")

# Process a specific event
event = ResendWebhookEvent.objects.get(event_id='some-id')
process_event(event)

# Process with custom handler
def my_handler(event):
    # Your custom processing logic
    if event.event_type == 'email.sent':
        print(f"Email sent: {event.email}")

process_pending_events(handler=my_handler)
```

#### Option 3: Using Celery (Recommended for Production)

Create a Celery task:

```python
# tasks.py
from celery import shared_task
from django_resend.utils import process_pending_events

@shared_task
def process_resend_webhooks():
    """Process pending Resend webhook events."""
    stats = process_pending_events(limit=100)
    return stats
```

Schedule it to run periodically:

```python
# celery.py or settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'process-resend-webhooks': {
        'task': 'your_app.tasks.process_resend_webhooks',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

### Event Model

The `ResendWebhookEvent` model stores all webhook data:

```python
from django_resend.models import ResendWebhookEvent

# Get pending events
pending = ResendWebhookEvent.objects.filter(status='pending')

# Get events by type
sent_emails = ResendWebhookEvent.objects.filter(event_type='email.sent')

# Access payload data
event = ResendWebhookEvent.objects.first()
email_data = event.get_payload_data()
```

### Event Status

Events have the following statuses:

- `pending`: Event received but not yet processed
- `processing`: Event is currently being processed
- `processed`: Event successfully processed
- `failed`: Event processing failed

### Retry Failed Events

```python
from django_resend.utils import retry_failed_events

# Retry failed events (max 3 retries by default)
stats = retry_failed_events(limit=50, max_retries=3)
```

## Django Admin

The package includes a Django admin interface for managing webhook events:

- View all events with filtering and search
- See event status with color-coded badges
- View full JSON payload
- Manually change event status
- Bulk actions for status changes

## Event Types

Resend sends various event types. Common ones include:

- `email.sent` - Email was sent
- `email.delivered` - Email was delivered
- `email.delivery_delayed` - Email delivery delayed
- `email.complained` - Recipient marked as spam
- `email.bounced` - Email bounced
- `email.opened` - Email was opened
- `email.clicked` - Link in email was clicked

All event data is stored in the `payload` JSONField for full access to Resend's event structure.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
