from django.contrib import admin
from .models import (
    Profile, TypedRole, SocialLink, Stat,
    SkillCategory, Skill,
    Experience, ExperienceProject, ExperienceAchievement, ExperienceTech,
    Project, ProjectTech,
    Education, EducationScore,
    ContactItem,
    Blog, BlogTag,
)


# ─── PROFILE ──────────────────────────────────────────────────────────────────

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "location")
    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "logo_text", "logo_image", "location", "eyebrow_text", "email", "phone", "resume_url"),
        }),
        ("Hero Section", {
            "fields": ("hero_description",),
        }),
        ("Summary / About Section", {
            "fields": ("summary_text",),
        }),
        ("Terminal Card", {
            "fields": ("terminal_role", "terminal_company", "terminal_stack", "terminal_ai_expertise"),
            "classes": ("collapse",),
        }),
        ("Marketing Funnel CTA", {
            "fields": ("funnel_is_active", "funnel_heading", "funnel_subheading", "funnel_button_text", "funnel_button_url"),
        }),
        ("Contact Section", {
            "fields": ("contact_heading", "contact_description"),
        }),
        ("AI Assistant", {
            "fields": ("ai_agent_name", "ai_agent_intro"),
        }),
    )

    def has_add_permission(self, request):
        # Only allow one Profile (singleton pattern)
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


# ─── TYPED ROLES ──────────────────────────────────────────────────────────────

@admin.register(TypedRole)
class TypedRoleAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    ordering = ("order",)


# ─── SOCIAL LINKS ─────────────────────────────────────────────────────────────

@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "order")
    list_editable = ("order",)
    ordering = ("order",)


# ─── STATS ────────────────────────────────────────────────────────────────────

@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ("label", "number", "show_plus", "order")
    list_editable = ("number", "show_plus", "order")
    ordering = ("order",)


# ─── SKILLS ───────────────────────────────────────────────────────────────────

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 2
    fields = ("name", "order")


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [SkillInline]


# ─── EXPERIENCE ───────────────────────────────────────────────────────────────

class ExperienceProjectInline(admin.StackedInline):
    model = ExperienceProject
    extra = 1
    fields = ("title", "description", "order")


class ExperienceAchievementInline(admin.TabularInline):
    model = ExperienceAchievement
    extra = 1
    fields = ("text", "order")


class ExperienceTechInline(admin.TabularInline):
    model = ExperienceTech
    extra = 3
    fields = ("name", "order")


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("company", "role", "start_date", "end_date", "is_current", "order")
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [ExperienceProjectInline, ExperienceAchievementInline, ExperienceTechInline]
    fieldsets = (
        (None, {
            "fields": ("company", "location", "role", "start_date", "end_date", "is_current", "intro_text", "order"),
        }),
    )


# ─── PROJECTS ─────────────────────────────────────────────────────────────────

class ProjectTechInline(admin.TabularInline):
    model = ProjectTech
    extra = 3
    fields = ("name", "order")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [ProjectTechInline]


# ─── EDUCATION ────────────────────────────────────────────────────────────────

class EducationScoreInline(admin.TabularInline):
    model = EducationScore
    extra = 1
    fields = ("label", "order")


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("institution", "degree", "date_range", "order")
    list_editable = ("order",)
    ordering = ("order",)
    inlines = [EducationScoreInline]


# ─── CONTACT ITEMS ────────────────────────────────────────────────────────────

@admin.register(ContactItem)
class ContactItemAdmin(admin.ModelAdmin):
    list_display = ("label", "url", "full_width", "order")
    list_editable = ("full_width", "order")
    ordering = ("order",)


# ─── BLOG ─────────────────────────────────────────────────────────────────────

class BlogTagInline(admin.TabularInline):
    model = BlogTag
    extra = 3
    fields = ("name", "order")


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("title", "published_date", "is_featured", "is_published", "order")
    list_editable = ("is_featured", "is_published", "order")
    list_filter = ("is_featured", "is_published", "published_date")
    search_fields = ("title", "content", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("order", "-published_date")
    inlines = [BlogTagInline]
