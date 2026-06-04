from .agent_services import (
    ResearchAgent,
    PortfolioAgent,
    ClientAgent,
    RecruiterAgent,
    ProjectExplainerAgent,
    RecommendationAgent,
)

AGENTS = {
    "research": ResearchAgent,
    "portfolio": PortfolioAgent,
    "client": ClientAgent,
    "recruiter": RecruiterAgent,
    "project_explainer": ProjectExplainerAgent,
    "recommendation": RecommendationAgent,
}


class AgentManager:

    @staticmethod
    def run(user, agent_type, query):

        agent_class = AGENTS.get(agent_type)

        if not agent_class:
            raise ValueError(
                f"Invalid agent type: {agent_type}"
            )

        agent = agent_class()

        return agent.execute(user,query)