from celery import shared_task
from datetime import datetime
from app.services.communication_service import CommunicationService

@shared_task
def send_daily_digest():
    """Send daily digest to stakeholders"""
    print("📊 Sending daily digest...")
    
    service = CommunicationService()
    
    # This would send summary emails
    return {"status": "digest_sent", "timestamp": datetime.utcnow().isoformat()}

@shared_task
def notify_urgent_risks():
    """Notify about urgent risks"""
    print("🚨 Notifying urgent risks...")
    
    # This would send urgent notifications
    return {"status": "urgent_notifications_sent", "timestamp": datetime.utcnow().isoformat()}