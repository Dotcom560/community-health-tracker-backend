import os
import logging
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class AlertService:
    """Multi-channel alert service for WhatsApp, Email, and SMS"""
    
    def __init__(self):
        # Initialize Twilio client for WhatsApp/SMS
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        
        # Initialize SendGrid for email
        self.sendgrid_client = None
        if settings.SENDGRID_API_KEY:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    
    def send_whatsapp_alert(self, to_number, message, alert_level='info'):
        """
        Send WhatsApp alert using Twilio WhatsApp Business API
        
        Args:
            to_number: Recipient phone number (e.g., '+233XXXXXXXXX')
            message: Alert message content
            alert_level: 'emergency', 'warning', or 'info'
        """
        if not self.twilio_client:
            logger.error("Twilio client not configured")
            return False
        
        try:
            # Format message with emoji based on alert level
            emoji = {
                'emergency': '🚨 URGENT EMERGENCY 🚨\n\n',
                'warning': '⚠️ Health Warning ⚠️\n\n',
                'info': 'ℹ️ Health Update\n\n'
            }.get(alert_level, '')
            
            full_message = emoji + message
            
            # Send WhatsApp message
            message = self.twilio_client.messages.create(
                body=full_message,
                from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
                to=f'whatsapp:{to_number}'
            )
            logger.info(f"WhatsApp alert sent to {to_number}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"WhatsApp alert failed: {e}")
            return False
    
    def send_email_alert(self, to_email, subject, message, alert_level='info'):
        """
        Send email alert using SendGrid or Django's email backend
        """
        try:
            if self.sendgrid_client:
                # Send via SendGrid
                mail = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=to_email,
                    subject=f"[{alert_level.upper()}] {subject}",
                    html_content=f"""
                    <html>
                        <head>
                            <style>
                                .alert-emergency {{ background-color: #dc3545; color: white; padding: 10px; }}
                                .alert-warning {{ background-color: #fd7e14; color: white; padding: 10px; }}
                                .alert-info {{ background-color: #007bff; color: white; padding: 10px; }}
                            </style>
                        </head>
                        <body>
                            <div class="alert-{alert_level}">
                                <h2>{subject}</h2>
                            </div>
                            <div style="padding: 20px;">
                                <p>{message}</p>
                                <hr>
                                <p><small>Community Health Tracker - Automated Alert</small></p>
                            </div>
                        </body>
                    </html>
                    """
                )
                response = self.sendgrid_client.send(mail)
                return response.status_code in [200, 202]
            else:
                # Fallback to Django email
                send_mail(
                    subject=f"[{alert_level.upper()}] {subject}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to_email],
                    fail_silently=False,
                )
                return True
                
        except Exception as e:
            logger.error(f"Email alert failed: {e}")
            return False
    
    def broadcast_alert(self, recipients, message, alert_level='info'):
        """
        Broadcast alert to multiple recipients via multiple channels
        """
        results = {
            'whatsapp_sent': 0,
            'email_sent': 0,
            'failed': 0
        }
        
        for recipient in recipients:
            if recipient.get('whatsapp'):
                if self.send_whatsapp_alert(recipient['whatsapp'], message, alert_level):
                    results['whatsapp_sent'] += 1
                else:
                    results['failed'] += 1
            
            if recipient.get('email'):
                subject = self._get_alert_subject(alert_level)
                if self.send_email_alert(recipient['email'], subject, message, alert_level):
                    results['email_sent'] += 1
                else:
                    results['failed'] += 1
        
        return results
    
    def _get_alert_subject(self, alert_level):
        """Generate subject line based on alert level"""
        subjects = {
            'emergency': '🚨 EMERGENCY HEALTH ALERT - Immediate Action Required',
            'warning': '⚠️ Health Warning - Please Review',
            'info': 'Health Information Update'
        }
        return subjects.get(alert_level, 'Community Health Tracker Alert')


# Singleton instance
alert_service = AlertService()


def send_outbreak_alert(outbreak_data):
    """Send alerts when outbreak is detected"""
    recipients = []  # Fetch from database - admin contacts
    
    message = f"""
    Outbreak Alert: {outbreak_data.get('category', 'Unknown')} symptoms detected
    
    Current rate: {outbreak_data.get('current_rate', 0)}%
    Baseline rate: {outbreak_data.get('baseline_rate', 0)}%
    
    Recommended action: {outbreak_data.get('action_required', 'Investigate')}
    
    Please log into the dashboard for more details.
    """
    
    return alert_service.broadcast_alert(
        recipients=recipients,
        message=message,
        alert_level=outbreak_data.get('level', 'warning')
    )