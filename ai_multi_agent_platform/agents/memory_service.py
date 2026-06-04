from .models import AgentMemory


class MemoryService:

    @staticmethod
    def get_memory(user, agent_type):

        memories = AgentMemory.objects.filter(
            user=user,
            agent_type=agent_type
        ).order_by("-created_at")[:5]

        return "\n".join(
            [m.memory for m in memories]
        )