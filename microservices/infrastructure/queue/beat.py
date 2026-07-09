from celery.schedules import crontab

beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "tasks.maintenance_tasks.cleanup_expired_sessions",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "maintenance"},
    },
    "cleanup-expired-idempotency-keys": {
        "task": "tasks.maintenance_tasks.cleanup_expired_idempotency_keys",
        "schedule": crontab(hour="*/6"),
        "options": {"queue": "maintenance"},
    },
    "health-check-workers": {
        "task": "tasks.maintenance_tasks.health_check_workers",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "maintenance"},
    },
    "collect-celery-metrics": {
        "task": "tasks.maintenance_tasks.collect_celery_metrics",
        "schedule": crontab(minute="*/1"),
        "options": {"queue": "maintenance"},
    },
    "reindex-portfolio-every-15min": {
        "task": "tasks.portfolio_sync.reindex_portfolio_if_changed",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "maintenance"},
    },
}
