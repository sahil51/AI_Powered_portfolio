from .agent_services import (
    PortfolioAgent,
    RecruiterAgent,
    RecommendationAgent,
)


class AgentCrew:

    @staticmethod
    def execute(user, query):

        portfolio_result = (
            PortfolioAgent()
            .execute(
                user,
                query
            )
        )

        recruiter_result = (
            RecruiterAgent()
            .execute(
                user,
                portfolio_result["result"]
            )
        )

        recommendation_result = (
            RecommendationAgent()
            .execute(
                user,
                recruiter_result["result"]
            )
        )

        return {
            "portfolio":
                portfolio_result["result"],

            "recruiter":
                recruiter_result["result"],

            "recommendation":
                recommendation_result["result"],
        }