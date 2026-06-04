from .manager import AgentManager


class AgentExecutor:

    @staticmethod
    def execute(user, agent_type, query):

        return AgentManager.run(
            user,
            agent_type,
            query
        )