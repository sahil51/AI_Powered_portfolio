from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from infrastructure.database.session import Base


class PortfolioHeroInfo(Base):
    __tablename__ = "portfolio_heroinfo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), default="Sahil Thakur")
    location = Column(String(200))
    current_company = Column(String(200))
    short_intro = Column(Text)
    email = Column(String(254))
    linkedin_url = Column(String(200))
    github_url = Column(String(200))
    portfolio_url = Column(String(200))
    terminal_title = Column(String(100))
    class_name = Column(String(100))
    role = Column(String(150))
    tech_stack = Column(String(255))
    ai_expertise = Column(String(255))
    open_to_work = Column(Boolean, default=True)
    resume = Column(String(100), nullable=True)
    experience_years = Column(Integer, default=2)
    ai_agents_built = Column(Integer, default=5)
    projects_completed = Column(Integer, default=10)
    about_me = Column(Text)
    phone = Column(String(50))
    contact_description = Column(Text)


class PortfolioProject(Base):
    __tablename__ = "portfolio_project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer)
    title = Column(String(150))
    description = Column(Text)
    icon_class = Column(String(100))
    technologies = Column(String(255))
    link = Column(String(200), nullable=True)


class PortfolioSkillCategory(Base):
    __tablename__ = "portfolio_skillcategory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    icon_class = Column(String(100))


class PortfolioSkill(Base):
    __tablename__ = "portfolio_skill"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=False)
    name = Column(String(100))


class PortfolioExperience(Base):
    __tablename__ = "portfolio_experience"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String(150))
    location = Column(String(150))
    role = Column(String(150))
    start_date = Column(String(50))
    end_date = Column(String(50))
    is_present = Column(Boolean, default=False)
    intro = Column(Text)
    key_contributions = Column(Text)
    company_projects = Column(Text, nullable=True)
    technologies = Column(String(255))


class PortfolioEducation(Base):
    __tablename__ = "portfolio_education"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution = Column(String(150))
    degree = Column(String(150))
    duration = Column(String(100))
    location = Column(String(150))
    scores = Column(Text)


class PortfolioBlogPost(Base):
    __tablename__ = "portfolio_blogpost"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200))
    slug = Column(String(200), unique=True)
    summary = Column(Text)
    content = Column(Text)
    created_at = Column(String(50), nullable=True)
    status = Column(String(10), default="Published")


class PortfolioContactMethod(Base):
    __tablename__ = "portfolio_contactmethod"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    value = Column(String(255))
    link = Column(String(255))
    icon_class = Column(String(100))
    order = Column(Integer, default=0)
    is_full_width = Column(Boolean, default=False)
