from django.db import models


# ─── PROFILE (Singleton — Hero + Summary + Footer) ────────────────────────────

class Profile(models.Model):
    """Main profile info — used across Hero, Summary, Footer, Contact CTA."""
    name = models.CharField(max_length=100, help_text="Full name (e.g. Sahil Thakur)")
    logo_text = models.CharField(max_length=10, default="ST", help_text="Short logo text for navbar (fallback)")
    logo_image = models.ImageField(upload_to="logos/", null=True, blank=True, help_text="Upload a logo image for the navbar")
    location = models.CharField(max_length=150, help_text="City, State, Country")
    eyebrow_text = models.CharField(max_length=100, default="Open to Opportunities", help_text="Small text above name in Hero")
    hero_description = models.TextField(help_text="Short paragraph in Hero section")
    summary_text = models.TextField(help_text="Longer summary paragraph in About section")
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    resume_url = models.URLField(blank=True, help_text="Link to resume PDF (external URL)")
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True, help_text="Upload resume PDF directly — AI will serve this link automatically")

    # Terminal card content
    terminal_role = models.CharField(max_length=100, default="Backend & AI Engineer")
    terminal_company = models.CharField(max_length=100, default="Crescaler R&D")
    terminal_stack = models.TextField(default="Python, FastAPI, Django, PostgreSQL, Docker, Redis", help_text="Comma-separated stack items for terminal card")
    terminal_ai_expertise = models.TextField(default="LangChain, CrewAI, RAG, LLM Dev, Agentic AI, n8n", help_text="Comma-separated AI tools for terminal card")

    # Contact section
    contact_heading = models.CharField(max_length=200, default="Let's Build Something Great.")
    contact_description = models.TextField(default="Open to full-time roles, freelance projects, and AI collaboration. Backend engineer ready to ship production-grade software. Reach out and let's talk.")

    # Marketing Funnel CTA
    funnel_is_active = models.BooleanField(default=True, help_text="Show the marketing funnel CTA section")
    funnel_heading = models.CharField(max_length=200, default="Ready to build something amazing?", help_text="Main heading for the CTA")
    funnel_subheading = models.TextField(default="Let's turn your ideas into scalable, robust software.", help_text="Subheading for the CTA")
    funnel_button_text = models.CharField(max_length=50, default="Start a Project", help_text="Text on the CTA button")
    funnel_button_url = models.CharField(max_length=200, default="#contact", help_text="URL or #id for the CTA button (e.g. mailto: or calendly link)")

    # AI Assistant
    ai_agent_name = models.CharField(max_length=50, default="Daisy", help_text="Name of your AI Assistant")
    ai_agent_intro = models.TextField(default="I can answer anything about Sahil — his experience, skills, projects, or how to get in touch.", help_text="Short introduction message for the AI Assistant")

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profile"

    def __str__(self):
        return self.name

    def terminal_stack_list(self):
        return [s.strip() for s in self.terminal_stack.split(",") if s.strip()]

    def terminal_ai_list(self):
        return [s.strip() for s in self.terminal_ai_expertise.split(",") if s.strip()]


# ─── TYPED ROLES (Hero typing animation) ──────────────────────────────────────

class TypedRole(models.Model):
    """Roles that cycle in the hero typing animation."""
    title = models.CharField(max_length=100, help_text="e.g. Backend Engineer")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


# ─── SOCIAL LINKS ─────────────────────────────────────────────────────────────

class SocialLink(models.Model):
    """Social links shown in hero and contact sections."""
    name = models.CharField(max_length=50, help_text="e.g. GitHub, LinkedIn")
    url = models.URLField()
    icon_svg = models.TextField(blank=True, help_text="SVG path markup for the icon (just the <path> d attribute or full <svg>)")
    icon_emoji = models.CharField(max_length=10, blank=True, help_text="Fallback emoji if no SVG")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


# ─── STATS BAR ────────────────────────────────────────────────────────────────

class Stat(models.Model):
    """Stats bar numbers (e.g. 6 Client Projects)."""
    number = models.PositiveIntegerField(help_text="Target number for counter animation")
    label = models.CharField(max_length=50, help_text="e.g. Client Projects")
    show_plus = models.BooleanField(default=False, help_text="Show + after number (e.g. 10+)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.number} {self.label}"


# ─── SKILLS ───────────────────────────────────────────────────────────────────

class SkillCategory(models.Model):
    """Skill card groups (e.g. Languages, Backend Development)."""
    title = models.CharField(max_length=100)
    icon_svg = models.TextField(blank=True, help_text="SVG path or full tag for the icon")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Skill Categories"

    def __str__(self):
        return self.title


class Skill(models.Model):
    """Individual skill tags within a category."""
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


# ─── EXPERIENCE ───────────────────────────────────────────────────────────────

class Experience(models.Model):
    """Work experience entries."""
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    role = models.CharField(max_length=150, help_text="e.g. Full Stack Developer — R&D Team")
    start_date = models.CharField(max_length=30, help_text="e.g. 8/2025")
    end_date = models.CharField(max_length=30, blank=True, default="Present")
    is_current = models.BooleanField(default=False, help_text="Show green 'Present' badge")
    intro_text = models.TextField(help_text="Short intro paragraph under the role")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.company} — {self.role}"

    def date_display(self):
        return f"{self.start_date} — {self.end_date}"


class ExperienceProject(models.Model):
    """Company project bullets under an experience entry."""
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=150)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ExperienceAchievement(models.Model):
    """Key contribution bullets under an experience entry."""
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name="achievements")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:80]


class ExperienceTech(models.Model):
    """Tech stack tags shown at the bottom of an experience entry."""
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name="techs")
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Experience Tech Tag"
        verbose_name_plural = "Experience Tech Tags"

    def __str__(self):
        return self.name


# ─── PROJECTS ─────────────────────────────────────────────────────────────────

class Project(models.Model):
    """Featured project cards."""
    title = models.CharField(max_length=150)
    icon_svg = models.TextField(blank=True, help_text="SVG path or full tag for the project icon")
    cover_image = models.ImageField(upload_to="project_covers/", null=True, blank=True, help_text="Cover image for the project (replaces icon if provided)")
    description = models.TextField()
    project_url = models.URLField(blank=True, help_text="Link to live project or repo")
    # AI Knowledge Base fields
    complexity_notes = models.TextField(
        blank=True,
        help_text="Describe challenges faced during this project — what was hard, what blocked you (AI will use this)"
    )
    solution_found = models.TextField(
        blank=True,
        help_text="Describe how you solved the challenges — your approach, tools used, breakthrough (AI will use this)"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ProjectTech(models.Model):
    """Tech stack tags for a project card."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="techs")
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Project Tech Tag"
        verbose_name_plural = "Project Tech Tags"

    def __str__(self):
        return self.name


# ─── EDUCATION ────────────────────────────────────────────────────────────────

class Education(models.Model):
    """Education cards."""
    badge_svg = models.TextField(blank=True, help_text="SVG for the badge icon")
    badge_text = models.CharField(max_length=50, help_text="e.g. Degree, Board Results")
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200, help_text="e.g. Bachelor of Vocational (Software Development)")
    date_range = models.CharField(max_length=50, help_text="e.g. Oct 2021 — Jul 2024")
    location = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Education"

    def __str__(self):
        return f"{self.institution} — {self.degree}"


class EducationScore(models.Model):
    """Score chips within an education card (e.g. 12th Board — 74%)."""
    education = models.ForeignKey(Education, on_delete=models.CASCADE, related_name="scores")
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label


# ─── CONTACT ITEMS ────────────────────────────────────────────────────────────

class ContactItem(models.Model):
    """Contact grid items (email, phone, LinkedIn, etc.)."""
    icon_svg = models.TextField(blank=True, help_text="SVG for the contact icon")
    label = models.CharField(max_length=150, help_text="Display text")
    url = models.URLField(help_text="Link URL (mailto:, tel:, https://...)")
    full_width = models.BooleanField(default=False, help_text="Span full width of grid")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label


# ─── BLOG ─────────────────────────────────────────────────────────────────────

class Blog(models.Model):
    """Blog posts — top 3 featured shown on homepage."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly version of title")
    excerpt = models.TextField(max_length=300, help_text="Short preview text (max 300 chars)")
    content = models.TextField(help_text="Full blog content (supports HTML)")
    cover_svg = models.TextField(blank=True, help_text="SVG icon for the blog card")
    cover_image = models.ImageField(upload_to="blog_covers/", null=True, blank=True, help_text="Cover image for the blog (replaces icon if provided)")
    reading_time = models.PositiveIntegerField(default=5, help_text="Estimated reading time in minutes")
    published_date = models.DateField()
    is_featured = models.BooleanField(default=False, help_text="Show on homepage (top 3 featured)")
    is_published = models.BooleanField(default=True, help_text="Only published blogs are visible")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-published_date"]

    def __str__(self):
        return self.title


class BlogTag(models.Model):
    """Tags for blog posts."""
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


# ─── WHATSAPP CHAT ────────────────────────────────────────────────────────────

class WhatsAppChat(models.Model):
    """Stores chat history for a specific WhatsApp number to maintain context."""
    phone_number = models.CharField(max_length=50, unique=True)
    history = models.JSONField(default=list, blank=True, help_text="JSON serialized chat history")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_updated"]

    def __str__(self):
        return f"Chat with {self.phone_number}"
