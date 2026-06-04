from services.llm_service import LLMService

from .models import (
    AgentExecution,
    AgentMemory,
)

from .memory_service import MemoryService

from .prompts import (
    RECRUITER_PROMPT,
    PORTFOLIO_PROMPT,
    PROJECT_EXPLAINER_PROMPT,
    CLIENT_PROMPT,
    RECOMMENDATION_PROMPT,
)


class ResearchAgent:

    def execute(self, user, query):

        prompt = f"""
You are a senior research analyst.

Research the following topic:

{query}

Provide:

1. Summary
2. Key Findings
3. Current Trends
4. Recommendations

Keep response structured.
"""

        result = LLMService.generate(prompt)

        AgentExecution.objects.create(
            agent_type="research",
            prompt=prompt,
            response=result
        )

        return {
            "agent": "research",
            "query": query,
            "result": result,
        }


class RecruiterAgent:

    def execute(self, user, query):

        prompt = RECRUITER_PROMPT.format(
            query=query
        )

        result = LLMService.generate(prompt)

        AgentExecution.objects.create(
            agent_type="recruiter",
            prompt=prompt,
            response=result
        )

        return {
            "agent": "recruiter",
            "query": query,
            "result": result,
        }


class PortfolioAgent:

    def execute(self, user, query):

        memory = MemoryService.get_memory(
            user,
            "portfolio"
        )

        prompt = f"""
Previous User Memory:

{memory}

Current Project:

{query}

Analyze this project and provide:

1. Strengths
2. Weaknesses
3. Improvements
4. Interview Readiness Score
"""

        result = LLMService.generate(
            prompt
        )

        AgentMemory.objects.create(
            user=user,
            agent_type="portfolio",
            memory=query
        )

        AgentExecution.objects.create(
            agent_type="portfolio",
            prompt=prompt,
            response=result
        )

        return {
            "agent": "portfolio",
            "query": query,
            "result": result,
        }


class ClientAgent:

    def execute(self, user, query):

        prompt = CLIENT_PROMPT.format(
            query=query
        )

        result = LLMService.generate(prompt)

        AgentExecution.objects.create(
            agent_type="client",
            prompt=prompt,
            response=result
        )

        return {
            "agent": "client",
            "query": query,
            "result": result,
        }


class ProjectExplainerAgent:

    def execute(self, user, query):

        prompt = PROJECT_EXPLAINER_PROMPT.format(
            query=query
        )

        result = LLMService.generate(prompt)

        AgentExecution.objects.create(
            agent_type="project_explainer",
            prompt=prompt,
            response=result
        )

        return {
            "agent": "project_explainer",
            "query": query,
            "result": result,
        }


class RecommendationAgent:

    def execute(self, user, query):

        prompt = RECOMMENDATION_PROMPT.format(
            query=query
        )

        result = LLMService.generate(prompt)

        AgentExecution.objects.create(
            agent_type="recommendation",
            prompt=prompt,
            response=result
        )

        return {
            "agent": "recommendation",
            "query": query,
            "result": result,
        }