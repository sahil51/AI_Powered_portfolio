from django.db import models
from django.conf import settings

# Create your models here.
class ResearchTask(models.Model):

    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('running', 'Running'),
    ('complete', 'Complete'),
    ('failed', 'Failed')
]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    title = models.CharField(max_length=255)
    agent_type = models.CharField(
        max_length=50,
        default="research"
    )
    query = models.TextField()

    result = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

class TaskLog(models.Model):

    task = models.ForeignKey(
        ResearchTask,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.task.title} - {self.status}"