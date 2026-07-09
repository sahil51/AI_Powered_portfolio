from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.portfolio_models import (
    PortfolioBlogPost,
    PortfolioContactMethod,
    PortfolioEducation,
    PortfolioExperience,
    PortfolioHeroInfo,
    PortfolioProject,
    PortfolioSkill,
    PortfolioSkillCategory,
)


class PortfolioDataService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_all(self) -> str:
        parts = []

        hero = await self._fetch_hero()
        if hero:
            parts.append(hero)

        experience = await self._fetch_experience()
        if experience:
            parts.append(experience)

        projects = await self._fetch_projects()
        if projects:
            parts.append(projects)

        skills = await self._fetch_skills()
        if skills:
            parts.append(skills)

        education = await self._fetch_education()
        if education:
            parts.append(education)

        contact = await self._fetch_contact()
        if contact:
            parts.append(contact)

        return "\n\n".join(parts)

    async def _fetch_hero(self) -> str | None:
        result = await self._session.execute(select(PortfolioHeroInfo).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None

        lines = [
            f"Name: {row.name}",
            f"Role: {row.role}",
            f"Location: {row.location}",
            f"Current Company: {row.current_company}",
            f"Short Intro: {row.short_intro}",
            f"About: {row.about_me}",
            f"Experience: {row.experience_years} years",
            f"AI Agents Built: {row.ai_agents_built}",
            f"Projects Completed: {row.projects_completed}",
            f"Tech Stack: {row.tech_stack}",
            f"AI Expertise: {row.ai_expertise}",
            f"Email: {row.email}",
            f"Phone: {row.phone}",
            f"LinkedIn: {row.linkedin_url}",
            f"GitHub: {row.github_url}",
            f"Portfolio: {row.portfolio_url}",
            f"Open to Work: {'Yes' if row.open_to_work else 'No'}",
        ]
        if row.contact_description:
            lines.append(f"Contact Note: {row.contact_description}")
        return "About Sahil:\n" + "\n".join(lines)

    async def _fetch_experience(self) -> str | None:
        result = await self._session.execute(select(PortfolioExperience).order_by(PortfolioExperience.start_date.desc()))
        rows = result.scalars().all()
        if not rows:
            return None

        parts = ["Work Experience:"]
        for exp in rows:
            end = "Present" if exp.is_present else exp.end_date
            parts.append(f"\n{exp.role} at {exp.company} ({exp.location})")
            parts.append(f"Period: {exp.start_date} - {end}")
            parts.append(f"Intro: {exp.intro}")

            if exp.key_contributions:
                parts.append("Key Contributions:")
                for line in exp.key_contributions.split("\n"):
                    stripped = line.strip()
                    if stripped:
                        parts.append(f"  - {stripped}")

            if exp.company_projects:
                parts.append("Company Projects:")
                for line in exp.company_projects.split("\n"):
                    stripped = line.strip()
                    if stripped:
                        parts.append(f"  - {stripped}")

            if exp.technologies:
                parts.append(f"Technologies: {exp.technologies}")

        return "\n".join(parts)

    async def _fetch_projects(self) -> str | None:
        result = await self._session.execute(select(PortfolioProject).order_by(PortfolioProject.number))
        rows = result.scalars().all()
        if not rows:
            return None

        parts = ["Projects:"]
        for proj in rows:
            parts.append(f"\nProject {proj.number}: {proj.title}")
            parts.append(f"Description: {proj.description}")
            parts.append(f"Technologies: {proj.technologies}")
            if proj.link:
                parts.append(f"Link: {proj.link}")

        return "\n".join(parts)

    async def _fetch_skills(self) -> str | None:
        result = await self._session.execute(select(PortfolioSkillCategory).order_by(PortfolioSkillCategory.id))
        categories = result.scalars().all()
        if not categories:
            return None

        parts = ["Skills:"]
        for cat in categories:
            skill_result = await self._session.execute(
                select(PortfolioSkill).where(PortfolioSkill.category_id == cat.id).order_by(PortfolioSkill.id)
            )
            skills = skill_result.scalars().all()
            skill_names = [s.name for s in skills]
            parts.append(f"\n{cat.name}:")
            parts.append(", ".join(skill_names))

        return "\n".join(parts)

    async def _fetch_education(self) -> str | None:
        result = await self._session.execute(select(PortfolioEducation))
        rows = result.scalars().all()
        if not rows:
            return None

        parts = ["Education:"]
        for edu in rows:
            parts.append(f"\n{edu.degree} at {edu.institution}")
            parts.append(f"Duration: {edu.duration}")
            parts.append(f"Location: {edu.location}")
            if edu.scores:
                parts.append("Scores:")
                for line in edu.scores.split("\n"):
                    stripped = line.strip()
                    if stripped:
                        parts.append(f"  - {stripped}")

        return "\n".join(parts)

    async def _fetch_contact(self) -> str | None:
        result = await self._session.execute(
            select(PortfolioContactMethod).order_by(PortfolioContactMethod.order)
        )
        rows = result.scalars().all()
        if not rows:
            return None

        parts = ["Contact Methods:"]
        for cm in rows:
            parts.append(f"  {cm.name}: {cm.value}")

        return "\n".join(parts)

    async def fetch_blog_posts(self) -> str | None:
        result = await self._session.execute(
            select(PortfolioBlogPost).where(PortfolioBlogPost.status == "Published").order_by(PortfolioBlogPost.id.desc())
        )
        rows = result.scalars().all()
        if not rows:
            return None

        parts = ["Blog Posts:"]
        for post in rows:
            parts.append(f"\n### {post.title}")
            parts.append(f"Summary: {post.summary}")

        return "\n".join(parts)
