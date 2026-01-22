"""
Configuration settings for django-resend package.
"""
from django.conf import settings


def get_resend_api_key():
    """
    Get Resend API key from Django settings.
    
    Returns:
        str: The Resend API key, or empty string if not set.
    """
    return getattr(settings, 'RESEND_APIKEY', '')


def get_resend_webhook_secret():
    """
    Get Resend webhook signing secret from Django settings.
    
    Returns:
        str: The webhook signing secret, or None if not set.
    """
    return getattr(settings, 'RESEND_WEBHOOK_SECRET', None)


def get_resend_webhook_timeout():
    """
    Get webhook timeout setting.
    
    Returns:
        int: Timeout in seconds (default: 30)
    """
    return getattr(settings, 'RESEND_WEBHOOK_TIMEOUT', 30)
