import os
import sys

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_project.settings")

import django
django.setup()

from portfolio.models import (
    HeroInfo,
    TypedRole,
    SkillCategory,
    Skill,
    Experience,
    Project,
    Education,
    BlogPost,
    Visitor,
    ContactMessage,
    ContactMethod,
)


def seed():
    print("[*] Starting Portfolio Update from Sahil_Thakur_AI_Engineer_Resume.pdf...")

    # 1. Clean out existing data
    ContactMessage.objects.all().delete()
    Visitor.objects.all().delete()
    BlogPost.objects.all().delete()
    Project.objects.all().delete()
    Experience.objects.all().delete()
    Skill.objects.all().delete()
    SkillCategory.objects.all().delete()
    TypedRole.objects.all().delete()
    ContactMethod.objects.all().delete()
    HeroInfo.objects.all().delete()
    print("  ✓ Old data cleared.")

    # 2. HeroInfo (Summary & Bio from Resume)
    print("  -> Creating HeroInfo...")
    hero = HeroInfo.objects.create(
        name="Sahil Thakur",
        brand_name="Sahil Thakur",
        location="Ambala City, Haryana, India",
        current_company="Crescaler",
        role="Backend & AI Engineer",
        tech_stack="Python, Django, FastAPI, PostgreSQL, Redis, Docker",
        ai_expertise="LangChain, CrewAI, Agentic AI, RAG, LLM Integration, LLM Development, Chatbot Development, Prompt Engineering, n8n",
        short_intro="Backend & AI Engineer skilled in Python, Django, FastAPI, PostgreSQL, Redis, Docker, and Agentic AI. Experienced in building scalable APIs, automation systems, RAG applications, and AI-powered solutions.",
        about_me=(
            "Backend & AI Engineer skilled in Python, Django, FastAPI, PostgreSQL, Redis, Docker, and Agentic AI. "
            "Experienced in building scalable APIs, automation systems, RAG applications, and AI-powered solutions. "
            "Strong focus on backend architecture, performance optimization, and production-ready software development."
        ),
        email="sahilrajput5321@gmail.com",
        phone="+91 7404304607",
        linkedin_url="https://www.linkedin.com/in/sahil-thakur-401490218/",
        github_url="https://github.com/sahil51",
        portfolio_url="https://sahilthakur.dev",
        resume="resumes/Sahil_Thakur_AI_Engineer_Resume.pdf",
        terminal_title="sahil_profile.py",
        class_name="SahilThakur",
        experience_years=2,
        ai_agents_built=5,
        projects_completed=10,
        open_to_work=True,
        contact_description="Backend & AI Engineer ready to ship production-grade software. Reach out and let's talk.",
    )

    # 3. Typed Roles
    print("  -> Creating Typed Roles...")
    roles = [
        "Backend & AI Engineer",
        "Full Stack Developer",
        "Agentic AI & RAG Engineer",
        "Microservices Architect",
    ]
    for r in roles:
        TypedRole.objects.create(name=r)

    # 4. Skills (Exact from Resume)
    print("  -> Creating Skills and Categories...")
    skills_map = {
        "Languages": (
            "fa-solid fa-code",
            ["Python", "JavaScript", "HTML", "CSS"],
        ),
        "Backend Development": (
            "fa-solid fa-server",
            ["Django", "FastAPI", "Flask", "REST APIs", "Microservices"],
        ),
        "AI & Automation": (
            "fa-solid fa-robot",
            [
                "LangChain",
                "CrewAI",
                "Agentic AI",
                "RAG",
                "LLM Integration",
                "LLM Development",
                "Chatbot Development",
                "Prompt Engineering",
                "n8n",
            ],
        ),
        "Databases & DevOps": (
            "fa-solid fa-database",
            [
                "PostgreSQL",
                "MySQL",
                "Redis",
                "Docker",
                "Nginx",
                "PM2",
                "Git",
                "Linux Server Management",
                "Supervisor",
            ],
        ),
        "Tools and Technologies": (
            "fa-solid fa-screwdriver-wrench",
            [
                "WordPress",
                "Strapi CMS",
                "Tailwind CSS",
                "Bootstrap",
                "NumPy",
                "Pandas",
                "Matplotlib",
                "Cursor",
                "Claude Code",
                "Codex",
                "Kiro",
                "Ollama",
            ],
        ),
    }

    for cat_name, (icon, items) in skills_map.items():
        cat = SkillCategory.objects.create(name=cat_name, icon_class=icon)
        for s in items:
            Skill.objects.create(category=cat, name=s)

    # 5. Experience (Exact from Resume)
    print("  -> Creating Experience...")
    Experience.objects.create(
        company="Crescaler",
        location="Ambala City, Haryana",
        role="Full Stack Developer – R&D Team",
        start_date="8/2025",
        end_date="Present",
        is_present=True,
        intro="Built and maintained web applications, AI-powered platforms, microservices, and automation solutions using Next.js, FastAPI, WordPress, Strapi, Gemini AI, and n8n.",
        company_projects=(
            "Kailasham by Shivrattan: Headless e-commerce platform built using Next.js, WordPress, and Razorpay with authentication, cart, and payment integration.\n"
            "Akash Infra: Managed production deployments, server configuration, SSL setup, and application releases on Ubuntu VPS servers.\n"
            "Frenchyard: Developed a FastAPI-based microservice for document management with direct cloud storage integration.\n"
            "CELPIP: AI Assessment Platform: Built an AI-powered system using FastAPI and Gemini AI for speaking and writing assessment through image and audio analysis."
        ),
        key_contributions=(
            "Built AI agents, RAG chatbots, lead generation systems, content automation pipelines, and workflow monitoring solutions using n8n and Gemini AI.\n"
            "Managed deployments, server optimization, monitoring, and release processes using Ubuntu, Nginx, PM2, and modern DevOps practices."
        ),
        technologies="Next.js, FastAPI, WordPress, Strapi, Gemini AI, n8n, Ubuntu, Nginx, PM2, Docker, Redis",
    )

    # 6. Technical Blogs (explaining the core architecture in resume)
    print("  -> Creating Blog Articles...")
    blog1 = BlogPost.objects.create(
        title="Architecting Enterprise Automation Pipelines: Deep-Dive into n8n, Django Microservices, and AI Workflows",
        slug="enterprise-automation-pipelines-n8n-django-ai",
        category="Architecture & AI",
        author="Sahil Thakur",
        source="Crescaler Engineering",
        status="Published",
        summary="A deep architectural breakdown of building decoupled, event-driven 4-tier microservice architectures connecting Django, autonomous AI agents, Telegram webhooks, and n8n workflow automation.",
        content="""<h2>1. System Vision & Architectural Trade-Offs</h2>
<p>Modern enterprise applications require seamless, real-time bridges between client-facing web interfaces, backend microservices, autonomous artificial intelligence agents, and external third-party communication channels. In building an enterprise AI-powered portfolio platform, the primary engineering objective was eliminating administrative overhead while maintaining a scalable, production-grade, zero-downtime microservices architecture.</p>

<h3>The Monolithic Automation Anti-Pattern vs Decoupled Microservices</h3>
<p>In traditional monolithic architectures, background tasks like media transformation, natural language AI processing, third-party API polling, and calendar synchronization are executed either in the main thread (blocking web requests) or pushed to heavy worker queues. This introduces significant operational challenges:</p>
<ul>
  <li><strong>Resource Starvation:</strong> Heavy CPU cycles slow down database transactions and web page delivery.</li>
  <li><strong>Third-Party API Vulnerability:</strong> Rate limits, token expirations, or external service outages cause uncaught exceptions in the primary web server.</li>
  <li><strong>Tightly Coupled Deployment:</strong> Any modification to a third-party webhook requires updating and redeploying the core web application codebase.</li>
</ul>
<p>To solve these challenges, I engineered a decoupled, event-driven 4-tier microservices architecture delegating orchestration to <strong>n8n Workflow Automation</strong> while keeping the <strong>Django Core Backend</strong> and <strong>AI Subsystems</strong> lightweight and focused purely on domain logic.</p>

<h2>2. High-Level Architecture (4-Tier Decoupling)</h2>
<p>The platform separates responsibilities cleanly:</p>
<ol>
  <li><strong>Frontend Tier:</strong> Responsive UI with custom design tokens, micro-animations, and interactive AI chat.</li>
  <li><strong>Core Backend (Django):</strong> Content modeling, admin governance, and secure API key authentication.</li>
  <li><strong>AI Microservice (FastAPI):</strong> Conversational agent routing, RAG retrieval, and natural language entity extraction.</li>
  <li><strong>Automation Tier (n8n):</strong> Telegram webhook listeners, image processing, and Google Calendar scheduling.</li>
</ol>""",
    )

    blog2 = BlogPost.objects.create(
        title="Building Production-Grade RAG Chatbots with Python and Gemini Embeddings",
        slug="production-rag-chatbots-python-gemini",
        category="Artificial Intelligence",
        author="Sahil Thakur",
        source="AI Engineering Notes",
        status="Published",
        summary="How to build lightweight, zero-latency in-memory vector search engines using Gemini embeddings, hybrid cosine similarity, and keyword fallbacks for modern web applications.",
        content="""<h2>1. In-Memory Vector Search with Hybrid Retrieval</h2>
<p>By leveraging Google's <code>gemini-embedding-001</code> model, document embeddings are pre-computed and stored directly in lightweight memory structures. At query time, cosine similarity is computed in single-digit milliseconds:</p>
<pre><code>def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if (na and nb) else 0.0
</code></pre>

<h2>2. Multi-LLM Resilience & Fallbacks</h2>
<p>Combining high-speed primary inference (Cerebras) with intelligent fallback models (Gemini Flash & NVIDIA Nemotron) ensures 99.9% uptime and zero chat disruptions.</p>""",
    )

    # 7. Projects (Exact projects from Resume)
    print("  -> Creating Projects...")
    Project.objects.create(
        number=1,
        title="AI-Powered Portfolio & Autonomous Assistant (Daisy AI)",
        description=(
            "Engineered Decoupled Microservice System: Built a high-performance portfolio & CMS using Django integrated "
            "with an asynchronous FastAPI microservice powering an AI assistant (Daisy AI).\n\n"
            "Multi-LLM Fallback & Hybrid RAG Engine: Designed a RAG pipeline utilizing Google Gemini Embeddings and "
            "Cosine Similarity with a multi-tiered LLM fallback system (Cerebras -> Gemini -> NVIDIA API) for 99.9% availability.\n\n"
            "Automated Workflow Integrations: Created n8n webhooks for automated Telegram-to-Blog publishing and built an "
            "interactive meeting scheduling agent with real-time slot verification and SMTP email notifications.\n\n"
            "Enterprise Security & Performance: Implemented constant-time SHA-256 API key hashing, in-memory IP rate limiting, "
            "and CORS security policies for internal microservice communications."
        ),
        icon_class="fa-solid fa-robot",
        technologies="Python, Django, FastAPI, PostgreSQL/SQLite, RAG, Gemini Embeddings, Cerebras (LLaMA 3), n8n, Docker, REST APIs",
        link="https://github.com/sahil51/AI_Powered_portfolio",
        blog_post=blog1,
    )

    Project.objects.create(
        number=2,
        title="CELPIP: AI Assessment Platform",
        description=(
            "Built an AI-powered system using FastAPI and Gemini AI for speaking and writing assessment through "
            "image and audio analysis. Provides instant real-time band scores, grammar analysis, and structural suggestions."
        ),
        icon_class="fa-solid fa-graduation-cap",
        technologies="FastAPI, Gemini AI, Python, REST APIs, Audio Analysis",
        link="",
        blog_post=blog2,
    )

    Project.objects.create(
        number=3,
        title="Kailasham by Shivrattan",
        description=(
            "Headless e-commerce platform built using Next.js, WordPress, and Razorpay with secure authentication, "
            "cart state management, and real-time payment integration."
        ),
        icon_class="fa-solid fa-cart-shopping",
        technologies="Next.js, WordPress, Razorpay, REST APIs, Tailwind CSS",
        link="",
    )

    Project.objects.create(
        number=4,
        title="Frenchyard Document Microservice",
        description=(
            "Developed a FastAPI-based microservice for document management with direct cloud storage integration, "
            "asynchronous file handling, and automated metadata indexing."
        ),
        icon_class="fa-solid fa-cloud-arrow-up",
        technologies="FastAPI, Python, Cloud Storage, REST APIs, Docker",
        link="",
    )

    # 8. Education (Exact from Resume)
    print("  -> Creating Education...")
    Education.objects.create(
        institution="S.D College, Ambala Cantt, Haryana",
        degree="Bachelor of Vocational (Software Development)",
        duration="Oct,2021 - Jul,2024",
        location="Ambala Cantt, Haryana",
        scores=(
            "Year-2019 | 12th Board HBSE | 74%\n"
            "Year-2017 | 10th Board HBSE | 79%"
        ),
    )

    # 9. Contact Methods (Exact from Resume Header)
    print("  -> Creating Contact Methods...")
    ContactMethod.objects.create(
        name="Email",
        value="sahilrajput5321@gmail.com",
        link="mailto:sahilrajput5321@gmail.com",
        icon_class="fa-solid fa-envelope",
        order=1,
        is_full_width=False,
    )
    ContactMethod.objects.create(
        name="Phone / WhatsApp",
        value="+91 7404304607",
        link="https://wa.me/917404304607",
        icon_class="fa-brands fa-whatsapp",
        order=2,
        is_full_width=False,
    )
    ContactMethod.objects.create(
        name="LinkedIn",
        value="linkedin.com/in/sahil-thakur",
        link="https://www.linkedin.com/in/sahil-thakur-401490218/",
        icon_class="fa-brands fa-linkedin",
        order=3,
        is_full_width=False,
    )
    ContactMethod.objects.create(
        name="GitHub",
        value="github.com/sahil51",
        link="https://github.com/sahil51",
        icon_class="fa-brands fa-github",
        order=4,
        is_full_width=False,
    )
    ContactMethod.objects.create(
        name="Portfolio",
        value="sahilthakur.dev",
        link="https://sahilthakur.dev",
        icon_class="fa-solid fa-globe",
        order=5,
        is_full_width=False,
    )

    print("\n[✓] Portfolio successfully updated with 100% real data from Sahil_Thakur_AI_Engineer_Resume.pdf!")


if __name__ == "__main__":
    seed()
