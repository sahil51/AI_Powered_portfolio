from asyncio import taskgroups
from celery import shared_task
from .models import ResearchTask, TaskLog
from notifications.models import Notification

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from agents.executor import AgentExecutor


@shared_task
def process_research_task(task_id):

    task = ResearchTask.objects.get(id=task_id)

    # Running Status
    task.status = "running"
    task.save()

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "tasks",
        {
            "type": "task_update",
            "message": {
                "task_id": task.id,
                "status": "running",
            },
        },
    )

    TaskLog.objects.create(
        task=task,
        status="running"
    )

    try:

        response = AgentExecutor.execute(
            task.owner,
            task.agent_type,
            task.query
        )


        task.result = response["result"]
        task.status = "complete"
        task.save()

    except Exception as e:

        task.status = "failed"
        task.result = str(e)
        task.save()

    raise

    async_to_sync(channel_layer.group_send)(
        "tasks",
        {
            "type": "task_update",
            "message": {
                "task_id": task.id,
                "status": "complete",
                "result": task.result,
            },
        },
    )

    TaskLog.objects.create(
        task=task,
        status="complete"
    )

    Notification.objects.create(
        user=task.owner,
        title="Task Completed",
        message=f"{task.title} completed successfully",
    )

    return f"Task {task_id} completed"