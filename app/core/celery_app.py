from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "control_tower",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.monitoring", "app.tasks.notifications"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "monitor-shipments-every-30-seconds": {
            "task": "app.tasks.monitoring.monitor_all_shipments",
            "schedule": 30.0,
        },
        "check-risk-updates-every-minute": {
            "task": "app.tasks.monitoring.check_risk_updates",
            "schedule": 60.0,
        },
        "send-daily-digest": {
            "task": "app.tasks.notifications.send_daily_digest",
            "schedule": 86400.0,
        },
    }
)