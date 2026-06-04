from .models import ResearchTask


def create_task(user, data):

    task = ResearchTask.objects.create(
        owner=user,
        title=data['title'],
        query=data['query'],
        agent_type=data.get(
            'agent_type',
            'research'
        ),
        status='pending'
    )

    return task