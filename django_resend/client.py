"""
Resend API client wrapper for Django.

Provides a simple interface to send emails using Resend API.
"""
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from .conf import get_resend_api_key

try:
    import resend
except ImportError:
    resend = None

logger = logging.getLogger(__name__)


class ResendClient:
    """
    Client for interacting with Resend API.
    
    Usage:
        from django_resend.client import ResendClient
        
        client = ResendClient()
        client.send_email(
            to='user@example.com',
            subject='Hello',
            html='<p>Hello World</p>'
        )
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Resend client.
        
        Args:
            api_key: Resend API key. If not provided, uses RESEND_APIKEY setting.
        """
        if resend is None:
            raise ImportError(
                "resend package is not installed. "
                "Install it with: pip install resend"
            )
        
        self.api_key = api_key or get_resend_api_key()
        if not self.api_key:
            raise ValueError(
                "Resend API key is required. "
                "Set RESEND_APIKEY in your Django settings or pass api_key parameter."
            )
        
        resend.api_key = self.api_key
    
    def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str | List[str]] = None,
        cc: Optional[str | List[str]] = None,
        bcc: Optional[str | List[str]] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email via Resend.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            html: HTML content of the email
            text: Plain text content of the email
            from_email: Sender email address (uses default domain if not provided)
            reply_to: Reply-to email address(es)
            cc: CC email address(es)
            bcc: BCC email address(es)
            tags: List of tags for tracking
            attachments: List of attachment dictionaries
            headers: Custom email headers
            **kwargs: Additional parameters passed to Resend API
            
        Returns:
            dict: Response from Resend API containing message ID and status
            
        Raises:
            Exception: If email sending fails
        """
        params = {
            'to': to if isinstance(to, list) else [to],
            'subject': subject,
        }
        
        if html:
            params['html'] = html
        if text:
            params['text'] = text
        if from_email:
            params['from'] = from_email
        if reply_to:
            params['reply_to'] = reply_to if isinstance(reply_to, list) else [reply_to]
        if cc:
            params['cc'] = cc if isinstance(cc, list) else [cc]
        if bcc:
            params['bcc'] = bcc if isinstance(bcc, list) else [bcc]
        if tags:
            params['tags'] = tags
        if attachments:
            params['attachments'] = attachments
        if headers:
            params['headers'] = headers
        
        # Add any additional kwargs
        params.update(kwargs)
        
        try:
            response = resend.Emails.send(params)
            logger.info(f"Email sent successfully: {response.get('id')}")
            return response
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def get_email(self, email_id: str) -> Dict[str, Any]:
        """
        Get email details by ID.
        
        Args:
            email_id: Resend email ID
            
        Returns:
            dict: Email details from Resend API
        """
        try:
            response = resend.Emails.get(email_id)
            return response
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {e}")
            raise


# Convenience function
def send_email(
    to: str | List[str],
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to send an email using Resend.
    
    Usage:
        from django_resend.client import send_email
        
        send_email(
            to='user@example.com',
            subject='Hello',
            html='<p>Hello World</p>'
        )
    """
    client = ResendClient()
    return client.send_email(to=to, subject=subject, html=html, text=text, **kwargs)
