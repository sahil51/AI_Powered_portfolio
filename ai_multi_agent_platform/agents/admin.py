from django.contrib import admin
from .models import Agent, AgentExecution


admin.site.register(Agent)


@admin.register(AgentExecution)
class AgentExecutionAdmin(admin.ModelAdmin):

    list_display = (
        "agent_type",
        "created_at",
    )

    search_fields = (
        "agent_type",
    )