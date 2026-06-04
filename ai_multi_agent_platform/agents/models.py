from django.conf import settings
from django.db import models


class Agent(models.Model):

    AGENT_TYPES = [
    ('research', 'Research'),
    ('portfolio', 'Portfolio'),
    ('client', 'Client'),
    ('project_explainer', 'Project Explainer'),
    ('recruiter', 'Recruiter'),
]
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agents'
    )

    name = models.CharField(max_length=100)

    role = models.CharField(
        max_length=50,
        choices=AGENT_TYPES
    )

    goal = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

class AgentExecution(models.Model):

    agent_type = models.CharField(
        max_length=100
    )

    prompt = models.TextField()

    response = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.agent_type} - {self.created_at}"

class AgentMemory(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    agent_type = models.CharField(
        max_length=100
    )

    memory = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.agent_type} - {self.user.username}"