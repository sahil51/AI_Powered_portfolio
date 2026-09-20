from django.core.management.base import BaseCommand
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


class Command(BaseCommand):
    help = "Wipes old/test portfolio data and seeds complete, clean, real production data for Sahil Thakur."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting complete portfolio data wipe..."))

        # 1. Wipe Old Data
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

        self.stdout.write(self.style.SUCCESS("✓ All old and test data wiped successfully."))

        # 2. Seed HeroInfo
        self.stdout.write("Seeding HeroInfo...")
        hero = HeroInfo.objects.create(
            name="Sahil Thakur",
            brand_name="Sahil Thakur",
            location="Ambala City, Haryana, India",
            current_company="Crescaler R&D",
            role="Backend & AI Engineer",
            tech_stack="Python, FastAPI, Django, PostgreSQL, Docker, Redis, Celery",
            ai_expertise="LangChain, CrewAI, Agentic AI, RAG Systems, Gemini, n8n Automation",
            short_intro="Backend & AI Engineer specializing in Python, Django, FastAPI, PostgreSQL, Redis, Docker, and Agentic AI workflows. Experienced in architecting scalable microservices, intelligent RAG pipelines, and automated enterprise solutions.",
            about_me=(
                "I am a Backend & AI Engineer with hands-on experience in architecting scalable web applications, "
                "asynchronous microservices, and AI-powered automation systems. My core expertise centers on the Python "
                "ecosystem (Django, FastAPI), relational and vector database modeling (PostgreSQL), and modern Agentic AI "
                "workflows (LangChain, CrewAI, RAG, and n8n). I focus on building resilient, production-ready software with "
                "robust security, high throughput, and zero-downtime deployments."
            ),
            email="sahilrajput5321@gmail.com",
            phone="+91 7404304607",
            linkedin_url="https://www.linkedin.com/in/sahil-thakur-401490218/",
            github_url="https://github.com/sahil51",
            portfolio_url="https://sahilthakur.dev",
            experience_years=2,
            ai_agents_built=6,
            projects_completed=12,
            open_to_work=True,
            resume="resumes/Sahil_Thakur_AI_Engineer_Resume.pdf",
            terminal_title="sahil_profile.py",
            class_name="SahilThakur",

            contact_description="Open to full-time engineering roles, high-impact consulting, and AI collaboration. Ready to ship production-grade software.",
        )

        # 3. Seed Typed Roles
        self.stdout.write("Seeding Typed Roles...")
        roles = [
            "Backend Engineer",
            "AI & Automation Engineer",
            "Full Stack Developer",
            "Microservices Architect",
            "Agentic AI Specialist",
        ]
        for r in roles:
            TypedRole.objects.create(name=r)

        # 4. Seed Technical Skills & Categories
        self.stdout.write("Seeding Skill Categories and Skills...")
        skills_structure = {
            "Languages": ("fa-solid fa-code", ["Python", "JavaScript", "TypeScript", "SQL", "HTML5", "CSS3", "Bash"]),
            "Backend & Frameworks": ("fa-solid fa-server", ["Django", "FastAPI", "Flask", "RESTful APIs", "Microservices", "SQLAlchemy", "Celery", "Gunicorn", "Uvicorn"]),
            "AI & Automation": ("fa-solid fa-robot", ["Agentic AI", "LangChain", "CrewAI", "RAG Systems", "Google Gemini", "LLM Integration", "Prompt Engineering", "n8n Workflow Automation"]),
            "Databases & Caching": ("fa-solid fa-database", ["PostgreSQL", "Redis", "MySQL", "SQLite", "Connection Pooling", "Vector Search"]),
            "DevOps, Cloud & Linux": ("fa-solid fa-cloud", ["Docker", "Docker Compose", "Ubuntu Linux VPS", "Nginx Reverse Proxy", "PM2", "Render", "Git & GitHub", "SSL/TLS Hardening"]),
            "Tools & Methodologies": ("fa-solid fa-screwdriver-wrench", ["Postman", "Cursor", "VS Code", "NumPy", "Pandas", "Whitenoise", "Strapi CMS", "Agile & CI/CD"]),
        }

        for cat_name, (icon, skill_names) in skills_structure.items():
            cat = SkillCategory.objects.create(name=cat_name, icon_class=icon)
            for s_name in skill_names:
                Skill.objects.create(category=cat, name=s_name)

        # 5. Seed Experience
        self.stdout.write("Seeding Experience...")
        Experience.objects.create(
            company="Crescaler",
            location="Ambala City, Haryana, India",
            role="Full Stack & AI Engineer – R&D Team",
            start_date="Aug 2024",
            end_date="Present",
            is_present=True,
            intro="Leading the design, development, and deployment of production web applications, AI-driven automation workflows, and microservices for enterprise and client projects.",
            company_projects=(
                "Kailasham by Shivrattan — Production headless e-commerce platform built with Next.js, WordPress, and Razorpay with secure authentication, cart management, and payment reconciliation.\n"
                "CELPIP AI Assessment Platform — High-accuracy AI scoring engine built using FastAPI and Google Gemini for automated candidate speech and essay evaluation.\n"
                "Frenchyard Cloud Microservice — High-performance document processing and storage microservice integrated with cloud object storage.\n"
                "Akash Infra Infrastructure — Configured production Ubuntu VPS hosting, Nginx reverse proxy routing, automated SSL, and monitoring pipelines."
            ),
            key_contributions=(
                "Engineered autonomous AI agents, intelligent RAG pipelines, and automated lead generation workflows using n8n and Google Gemini AI.\n"
                "Designed resilient RESTful microservices with IP rate limiting, HMAC security verification, and asynchronous task processing.\n"
                "Managed production server infrastructure, zero-downtime releases, Nginx load balancing, and performance optimization on Linux environments."
            ),
            technologies="Python, FastAPI, Django, PostgreSQL, Next.js, Redis, Docker, n8n, Gemini AI, Nginx, PM2, Ubuntu Linux",
        )

        # 6. Seed Real Blog Articles
        self.stdout.write("Seeding Blog Articles...")
        blog1 = BlogPost.objects.create(
            title="Architecting Enterprise Automation Pipelines: Deep-Dive into n8n, Django Microservices, and AI Workflows",
            slug="enterprise-automation-pipelines-n8n-django-ai",
            category="Architecture & AI",
            author="Sahil Thakur",
            source="Crescaler Engineering",
            status="Published",
            summary=(
                "A deep architectural breakdown of building decoupled, event-driven 4-tier microservice architectures "
                "connecting Django, autonomous AI agents, Telegram webhooks, and n8n workflow automation."
            ),
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
</ol>

<h2>3. Security & Production Hardening</h2>
<p>All external webhooks communicate over TLS with constant-time HMAC header verification (<code>X-API-Key</code>), sliding-window IP rate limiting, and automated health checking to ensure rock-solid uptime.</p>""",
        )

        blog2 = BlogPost.objects.create(
            title="Building Production-Grade RAG Chatbots with Python and Gemini Embeddings",
            slug="production-rag-chatbots-python-gemini",
            category="Artificial Intelligence",
            author="Sahil Thakur",
            source="AI Engineering Notes",
            status="Published",
            summary=(
                "How to build lightweight, zero-latency in-memory vector search engines using Gemini embeddings, "
                "hybrid cosine similarity, and keyword fallbacks for modern web applications."
            ),
            content="""<h2>1. The Problem with Over-Engineered Vector Databases</h2>
<p>For high-performance portfolio sites and specialized business portals with under 10,000 documents, provisioning heavy external vector infrastructure (like Pinecone, Milvus, or Qdrant) introduces unnecessary network latency, billable tiers, and additional points of failure.</p>

<h2>2. In-Memory Vector Search with Hybrid Retrieval</h2>
<p>By leveraging Google's <code>gemini-embedding-001</code> model, document embeddings are pre-computed and stored directly in lightweight memory structures. At query time, cosine similarity is computed in single-digit milliseconds:</p>
<pre><code>def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if (na and nb) else 0.0
</code></pre>

<h2>3. Hybrid Keyword + Category Boosting Fallbacks</h2>
<p>Pure vector search occasionally misses precise terms like specific technical acronyms or model numbers. By combining semantic cosine scores with exact token overlap and category intent keywords, query retrieval achieves over 99% precision without hallucination.</p>""",
        )

        # 7. Seed Featured Projects (Linked to Real Articles)
        self.stdout.write("Seeding Featured Projects...")
        Project.objects.create(
            number=1,
            title="Autonomous AI Portfolio & Daisy Assistant",
            description=(
                "An enterprise-grade decoupled portfolio platform featuring Daisy, an autonomous conversational "
                "AI agent capable of multi-turn natural language interview scheduling, dynamic RAG vector search, "
                "and dual-party confirmation email dispatches."
            ),
            icon_class="fa-solid fa-robot",
            technologies="Python, Django, FastAPI, PostgreSQL, Gemini AI, Docker, Gunicorn, Vanilla CSS",
            link="https://github.com/sahil51/AI_Powered_portfolio",
            blog_post=blog1,
        )

        Project.objects.create(
            number=2,
            title="CELPIP AI Assessment & Scoring Platform",
            description=(
                "An AI-powered assessment suite built using FastAPI and Google Gemini multimodal models to grade student "
                "spoken audio and written essays in real time, delivering instant band scores and actionable grammatical feedback."
            ),
            icon_class="fa-solid fa-graduation-cap",
            technologies="FastAPI, Python, Gemini 2.5 Flash, Multimodal AI, REST APIs",
            link="",
            blog_post=blog2,
        )

        Project.objects.create(
            number=3,
            title="Real-Time Video & Speech Clarity Analyzer",
            description=(
                "A real-time communication analysis tool analyzing live video feeds for facial cues (smile percentage), "
                "filler words, speech pauses, and clarity, producing actionable improvement metrics and refined spoken text."
            ),
            icon_class="fa-solid fa-video",
            technologies="Node.js, React.js, Express, NLP, WebSockets",
            link="",
        )

        Project.objects.create(
            number=4,
            title="Enterprise n8n Automation & Webhook Pipelines",
            description=(
                "A decoupled automation pipeline orchestrating Telegram bot inputs, Google Calendar OAuth event creation, "
                "Google Gemini content polishers, and Django webhook endpoints for zero-downtime publishing."
            ),
            icon_class="fa-solid fa-network-wired",
            technologies="n8n, Docker, Webhooks, Telegram API, Google Calendar API, PostgreSQL",
            link="",
            blog_post=blog1,
        )

        # 8. Seed Education
        self.stdout.write("Seeding Education...")
        Education.objects.create(
            institution="S.D. College",
            degree="Bachelor of Vocational (Software Development)",
            duration="Oct 2021 — Jul 2024",
            location="Ambala Cantt, Haryana, India",
            scores=(
                "Bachelor of Vocational in Software Development (B.Voc) — First Class\n"
                "12th Senior Secondary (HBSE) — 74%\n"
                "10th Secondary (HBSE) — 79%"
            ),
        )

        # 9. Seed Contact Methods
        self.stdout.write("Seeding Contact Methods...")
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

        # 10. Seed Clean Sample Visitors
        self.stdout.write("Seeding Sample Verified Visitors...")
        Visitor.objects.create(
            name="Vikram Mehta",
            company="Nexus Cloud Labs",
            purpose="Discuss Full-Stack AI Engineer contract for enterprise automation pipeline",
            connection_info_type="online",
            connection_info_detail="Google Meet (Confirmed)",
            timing="Next Wednesday, 4:00 PM IST",
        )
        Visitor.objects.create(
            name="Pooja Sharma",
            company="Apex Talent Acquisition",
            purpose="Technical Interview discussion for Senior Backend & AI Engineer role",
            connection_info_type="call",
            connection_info_detail="+91 98765 43210",
            timing="Friday, 2:30 PM IST",
        )

        self.stdout.write(self.style.SUCCESS("══════════════════════════════════════════════════════════════════"))
        self.stdout.write(self.style.SUCCESS("✓ SUCCESS: Entire portfolio database wiped and re-seeded with real data!"))
        self.stdout.write(self.style.SUCCESS("══════════════════════════════════════════════════════════════════"))
