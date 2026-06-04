from .models import Agent


def create_agent(user, data):

    agent = Agent.objects.create(
        owner=user,
        name=data['name'],
        role=data['role'],
        goal=data['goal']
    )

    return agent