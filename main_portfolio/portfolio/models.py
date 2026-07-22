from django.db import models
from django.utils.text import slugify

class TypedRole(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Typed Role"
        verbose_name_plural = "Typed Roles"

    def __str__(self):
        return self.name

class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=100, default='fa-solid fa-code')

    class Meta:
        verbose_name = "Skill Category"
        verbose_name_plural = "Skill Categories"

    def __str__(self):
        return self.name

class Skill(models.Model):
    category = models.ForeignKey(SkillCategory, related_name='skills', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Technical Skill"
        verbose_name_plural = "Technical Skills"

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class Experience(models.Model):
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    start_date = models.CharField(max_length=50)
    end_date = models.CharField(max_length=50, default='Present')
    is_present = models.BooleanField(default=False)
    intro = models.TextField()
    
    # Store newline-separated bullet points for simplicity
    key_contributions = models.TextField(help_text="Enter key contributions, one per line")
    company_projects = models.TextField(help_text="Enter company projects, one per line", blank=True)
    
    # Comma-separated list of technologies used
    technologies = models.CharField(max_length=255, help_text="Comma-separated list of technologies (e.g. Next.js, FastAPI)")

    class Meta:
        verbose_name = "Work Experience"
        verbose_name_plural = "Work Experiences"

    def get_key_contributions_list(self):
        return [line.strip() for line in self.key_contributions.split('\n') if line.strip()]

    def get_company_projects_list(self):
        return [line.strip() for line in self.company_projects.split('\n') if line.strip()]

    def get_technologies_list(self):
        return [tag.strip() for tag in self.technologies.split(',') if tag.strip()]

    def __str__(self):
        return f"{self.role} at {self.company}"

class Project(models.Model):
    number = models.IntegerField(help_text="Project display order number")
    title = models.CharField(max_length=150)
    description = models.TextField()
    icon_class = models.CharField(max_length=100, default='fa-solid fa-rocket')
    technologies = models.CharField(max_length=255, help_text="Comma-separated list of technologies")
    link = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Featured Project"
        verbose_name_plural = "Featured Projects"

    def get_technologies_list(self):
        return [tag.strip() for tag in self.technologies.split(',') if tag.strip()]

    def __str__(self):
        return f"Project {self.number}: {self.title}"

class Education(models.Model):
    institution = models.CharField(max_length=150)
    degree = models.CharField(max_length=150)
    duration = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    scores = models.TextField(help_text="Enter scores or details, one per line")

    class Meta:
        verbose_name = "Education Detail"
        verbose_name_plural = "Education Details"

    def get_scores_list(self):
        return [line.strip() for line in self.scores.split('\n') if line.strip()]

    def __str__(self):
        return f"{self.degree} at {self.institution}"

import re

class BlogPost(models.Model):
    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('Published', 'Published'),
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.TextField(blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    author = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = "Blog Article"
        verbose_name_plural = "Blog Articles"

    @property
    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return None

    def save(self, *args, **kwargs):
        if self.status:
            formatted_status = str(self.status).strip().capitalize()
            if formatted_status in ['Draft', 'Published']:
                self.status = formatted_status
        if not self.summary and self.content:
            clean_text = re.sub('<[^<]+?>', '', self.content)
            self.summary = clean_text[:180] + '...' if len(clean_text) > 180 else clean_text
        if not self.slug:
            base_slug = slugify(self.title) or 'blog-post'
            self.slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Visitor(models.Model):
    name = models.CharField(max_length=150)
    company = models.CharField(max_length=150, blank=True)
    purpose = models.TextField()
    connection_info_type = models.CharField(max_length=50, help_text="e.g. call, online, offline")
    connection_info_detail = models.CharField(max_length=255)
    timing = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Meeting Request"
        verbose_name_plural = "Meeting Requests"

    def __str__(self):
        return f"{self.name} from {self.company or 'N/A'}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email Message"
        verbose_name_plural = "Email Messages"

    def __str__(self):
        return f"Message from {self.name} ({self.email})"

class HeroInfo(models.Model):
    name = models.CharField(max_length=150, default="Sahil Thakur")
    location = models.CharField(max_length=200, default="Ambala City, Haryana, India")
    current_company = models.CharField(max_length=200, default="Crescaler R&D")
    short_intro = models.TextField(default="Backend & AI Engineer skilled in Python, Django, FastAPI, PostgreSQL, Redis, Docker, and Agentic AI.")
    email = models.EmailField(default="sahilrajput5321@gmail.com")
    linkedin_url = models.URLField(default="https://linkedin.com")
    github_url = models.URLField(default="https://github.com")
    portfolio_url = models.URLField(default="https://sahilthakur.dev")
    
    # Coding terminal box details
    terminal_title = models.CharField(max_length=100, default="profile.py")
    class_name = models.CharField(max_length=100, default="SahilThakur")
    role = models.CharField(max_length=150, default="Backend & AI Engineer")
    tech_stack = models.CharField(max_length=255, default="Python, FastAPI, Django, PostgreSQL, Docker, Redis", help_text="Comma-separated list of technologies")
    ai_expertise = models.CharField(max_length=255, default="LangChain, CrewAI, Agentic AI, RAG, LLM Integration, Prompt Engineering, n8n", help_text="Comma-separated list of AI skills")
    open_to_work = models.BooleanField(default=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, help_text="Upload your Resume/CV PDF")
    
    # Stats Counters
    experience_years = models.IntegerField(default=2)
    ai_agents_built = models.IntegerField(default=5)
    projects_completed = models.IntegerField(default=10)

    # About Me & Contact details
    about_me = models.TextField(default="Backend & AI Engineer skilled in Python, Django, FastAPI, PostgreSQL, Redis, Docker, and Agentic AI. Experienced in building scalable APIs, automation systems, RAG applications, and AI-powered solutions. Strong focus on backend architecture, performance optimization, and production-ready software development.")
    phone = models.CharField(max_length=50, default="+91 7404304607")
    contact_description = models.TextField(default="Open to full-time roles, freelance projects, and AI collaboration. Backend engineer ready to ship production-grade software. Reach out and let's talk.")



    class Meta:
        verbose_name = "Hero Info"
        verbose_name_plural = "Hero Info"

    def get_tech_stack_list(self):
        return [tag.strip() for tag in self.tech_stack.split(',') if tag.strip()]

    def get_ai_expertise_list(self):
        return [tag.strip() for tag in self.ai_expertise.split(',') if tag.strip()]

    def __str__(self):
        return f"Hero Info: {self.name}"

class ContactMethod(models.Model):
    ICON_CHOICES = (
        ('fa-solid fa-envelope', 'Email'),
        ('fa-solid fa-phone', 'Phone'),
        ('fa-brands fa-whatsapp', 'WhatsApp'),
        ('fa-brands fa-linkedin', 'LinkedIn'),
        ('fa-brands fa-github', 'GitHub'),
        ('fa-solid fa-link', 'Website'),
    )
    name = models.CharField(max_length=100, help_text="e.g. Email, Phone, WhatsApp")
    value = models.CharField(max_length=255, help_text="e.g. sahilrajput5321@gmail.com, +91 7404304607")
    link = models.CharField(max_length=255, help_text="e.g. mailto:email, tel:phone, https://...")
    icon_class = models.CharField(max_length=100, choices=ICON_CHOICES, default='fa-solid fa-link')
    order = models.IntegerField(default=0, help_text="Display order")
    is_full_width = models.BooleanField(default=False, help_text="Display as full width (100%) instead of half width (50%)")


    class Meta:
        verbose_name = "Contact Method"
        verbose_name_plural = "Contact Methods"
        ordering = ('order',)

    def __str__(self):
        return f"{self.name}: {self.value}"


