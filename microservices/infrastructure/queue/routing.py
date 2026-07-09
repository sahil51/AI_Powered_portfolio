from kombu import Exchange, Queue

default_exchange = Exchange("default", type="direct")
critical_exchange = Exchange("critical", type="direct")
memory_exchange = Exchange("memory", type="direct")
embedding_exchange = Exchange("embeddings", type="direct")
workflow_exchange = Exchange("workflow", type="direct")
notification_exchange = Exchange("notifications", type="direct")
meeting_exchange = Exchange("meetings", type="direct")
maintenance_exchange = Exchange("maintenance", type="direct")

task_queues = [
    Queue("default", default_exchange, routing_key="default"),
    Queue("critical", critical_exchange, routing_key="critical"),
    Queue("memory", memory_exchange, routing_key="memory"),
    Queue("embeddings", embedding_exchange, routing_key="embeddings"),
    Queue("workflow", workflow_exchange, routing_key="workflow"),
    Queue("notifications", notification_exchange, routing_key="notifications"),
    Queue("meetings", meeting_exchange, routing_key="meetings"),
    Queue("maintenance", maintenance_exchange, routing_key="maintenance"),
]

task_routes = {
    "tasks.meeting_tasks.*": {"queue": "meetings"},
    "tasks.notification_tasks.*": {"queue": "notifications"},
    "tasks.memory_tasks.*": {"queue": "memory"},
    "tasks.embedding_tasks.*": {"queue": "embeddings"},
    "tasks.workflow_tasks.*": {"queue": "workflow"},
    "tasks.maintenance_tasks.*": {"queue": "maintenance"},
    "tasks.critical_tasks.*": {"queue": "critical"},
}

task_annotations = {
    "tasks.meeting_tasks.schedule_meeting_task": {"rate_limit": "10/m"},
    "tasks.notification_tasks.send_notification_task": {"rate_limit": "30/m"},
}
