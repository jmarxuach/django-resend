import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import ResendWebhookEvent
from .signals import webhook_event_received

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def resend_webhook_view(request):
    """
    Webhook endpoint to receive Resend events.
    
    This view receives webhook POST requests from Resend, stores them
    in the database with 'pending' status, and returns a quick response
    to avoid webhook timeout issues. The consuming application can then
    process events asynchronously.
    
    Returns:
        JsonResponse: Success response with status 200
        HttpResponseBadRequest: If request is invalid
    """
    try:
        # Parse JSON payload
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return HttpResponseBadRequest(
                json.dumps({"error": "Invalid JSON payload"}),
                content_type="application/json"
            )
        
        # Extract event information
        event_id = data.get('id')
        event_type = data.get('type', '')
        event_data = data.get('data', {})
        
        if not event_id:
            logger.error("Missing event ID in webhook payload")
            return HttpResponseBadRequest(
                json.dumps({"error": "Missing event ID"}),
                content_type="application/json"
            )
        
        # Parse timestamp
        timestamp_str = data.get('created_at') or data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = parse_datetime(timestamp_str)
                if timestamp is None:
                    # Try parsing as Unix timestamp
                    timestamp = timezone.datetime.fromtimestamp(
                        float(timestamp_str),
                        tz=timezone.utc
                    )
            except (ValueError, TypeError):
                timestamp = timezone.now()
        else:
            timestamp = timezone.now()
        
        # Extract common fields
        email = event_data.get('to') or event_data.get('email') or event_data.get('recipient')
        if isinstance(email, list) and email:
            email = email[0]
        
        message_id = event_data.get('email_id') or event_data.get('message_id') or event_data.get('id')
        
        # Check if event already exists (idempotency)
        event, created = ResendWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                'event_type': event_type,
                'timestamp': timestamp,
                'email': email,
                'message_id': message_id,
                'payload': data,
                'status': ResendWebhookEvent.STATUS_PENDING,
            }
        )
        
        if not created:
            logger.info(f"Duplicate webhook event received: {event_id}")
            return JsonResponse({"status": "duplicate", "message": "Event already processed"})
        
        # Send signal for consuming apps to hook into
        webhook_event_received.send(
            sender=ResendWebhookEvent,
            event=event,
            payload=data
        )
        
        logger.info(f"Webhook event received: {event_type} - {event_id}")
        
        return JsonResponse({
            "status": "received",
            "event_id": event_id
        })
        
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return HttpResponseBadRequest(
            json.dumps({"error": "Internal server error"}),
            content_type="application/json",
            status=500
        )
