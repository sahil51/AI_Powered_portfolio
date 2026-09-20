from django.db import migrations

def seed_portfolio_data(apps, schema_editor):
    # Get models
    TypedRole = apps.get_model('portfolio', 'TypedRole')
    SkillCategory = apps.get_model('portfolio', 'SkillCategory')
    Skill = apps.get_model('portfolio', 'Skill')
    Experience = apps.get_model('portfolio', 'Experience')
    Project = apps.get_model('portfolio', 'Project')
    Education = apps.get_model('portfolio', 'Education')
    Visitor = apps.get_model('portfolio', 'Visitor')
    
    # 1. Typed Roles
    roles = ["Backend Engineer", "AI Engineer", "Full Stack Developer"]
    for role in roles:
        TypedRole.objects.create(name=role)
        
    # 2. Skill Categories and Skills
    skills_data = {
        "Languages": ("fa-solid fa-code", ["Python", "JavaScript", "HTML", "CSS"]),
        "Backend Development": ("fa-solid fa-code", ["Django", "FastAPI", "Flask", "REST APIs", "Microservices"]),
        "AI & Automation": ("fa-solid fa-code", ["LangChain", "CrewAI", "Agentic AI", "RAG", "LLM Integration", "LLM Development", "Chatbot Development", "Prompt Engineering", "n8n"]),
        "Databases & DevOps": ("fa-solid fa-code", ["PostgreSQL", "MySQL", "Redis", "Docker", "Nginx", "PM2", "Git", "Linux Server Management", "Supervisor"]),
        "Tools and Technologies": ("fa-solid fa-code", ["WordPress", "Strapi CMS", "Tailwind CSS", "Bootstrap", "NumPy", "Pandas", "Matplotlib", "Cursor", "Claude Code", "Codex", "Kiro", "Ollama"])
    }
    for category_name, (icon, skills) in skills_data.items():
        cat = SkillCategory.objects.create(name=category_name, icon_class=icon)
        for skill_name in skills:
            Skill.objects.create(category=cat, name=skill_name)
            
    # 3. Experience
    Experience.objects.create(
        company="Crescaler",
        location="Ambala City, Haryana",
        role="Full Stack Developer – R&D Team",
        start_date="8/2025",
        end_date="Present",
        is_present=True,
        intro="Built and maintained web applications, AI-powered platforms, microservices, and automation solutions using Next.js, FastAPI, WordPress, Strapi, Gemini AI, and n8n.",
        company_projects="Kailasham by Shivrattan — Headless e-commerce platform built using Next.js, WordPress, and Razorpay with authentication, cart, and payment integration.\nAkash Infra — Managed production deployments, server configuration, SSL setup, and application releases on Ubuntu VPS servers.\nFrenchyard — Developed a FastAPI-based microservice for document management with direct cloud storage integration.\nCELPIP (AI Assessment Platform) — Built an AI-powered system using FastAPI and Gemini AI for speaking and writing assessment through image and audio analysis.",
        key_contributions="Built AI agents, RAG chatbots, lead generation systems, content automation pipelines, and workflow monitoring solutions using n8n and Gemini AI.\nManaged deployments, server optimization, monitoring, and release processes using Ubuntu, Nginx, PM2, and modern DevOps practices.",
        technologies="Next.js,FastAPI,WordPress,Strapi,Gemini AI,n8n,Ubuntu,Nginx,PM2"
    )
    
    # 4. Projects
    Project.objects.create(
        number=1,
        title="Real-time Video Analysis Tool",
        description="Built a real-time video analysis tool using React.js, Node.js, and Express to detect smile percentage, filler words, and weak words, generating an improved spoken paragraph for better speech clarity.",
        icon_class="fa-solid fa-rocket",
        technologies="React.js,Node.js,Express",
        link=""
    )
    Project.objects.create(
        number=2,
        title="CELPIP AI Assessment Platform",
        description="An AI-powered system built using FastAPI and Gemini AI for speaking and writing assessment through image and audio analysis.",
        icon_class="fa-solid fa-rocket",
        technologies="FastAPI,Gemini AI,Python",
        link=""
    )
    
    # 5. Education
    Education.objects.create(
        institution="S.D College",
        degree="Bachelor of Vocational (Software Development)",
        duration="Oct 2021 — Jul 2024",
        location="Ambala Cantt, Haryana",
        scores="12th Board HBSE — 74%\n10th Board HBSE — 79%"
    )
    
    # 6. Visitors
    visitors_list = [
        ("Vikram Mehta", "Nexus Cloud Labs", "Discuss Full-Stack AI Engineer contract for enterprise automation pipeline", "online", "Google Meet", "Next Wednesday, 4:00 PM IST"),
        ("Pooja Sharma", "Apex Talent Acquisition", "Technical Interview discussion for Senior Backend & AI Engineer role", "call", "+91 98765 43210", "Friday, 2:30 PM IST"),
    ]
    for name, comp, purp, conn_type, detail, timing in visitors_list:
        Visitor.objects.create(
            name=name,
            company=comp,
            purpose=purp,
            connection_info_type=conn_type,
            connection_info_detail=detail,
            timing=timing
        )


def rollback_seed_data(apps, schema_editor):
    TypedRole = apps.get_model('portfolio', 'TypedRole')
    SkillCategory = apps.get_model('portfolio', 'SkillCategory')
    Experience = apps.get_model('portfolio', 'Experience')
    Project = apps.get_model('portfolio', 'Project')
    Education = apps.get_model('portfolio', 'Education')
    Visitor = apps.get_model('portfolio', 'Visitor')
    
    TypedRole.objects.all().delete()
    SkillCategory.objects.all().delete()
    Experience.objects.all().delete()
    Project.objects.all().delete()
    Education.objects.all().delete()
    Visitor.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_portfolio_data, reverse_code=rollback_seed_data),
    ]
