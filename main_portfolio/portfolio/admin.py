from django.contrib import admin
from .models import TypedRole, SkillCategory, Skill, Experience, Project, Education, BlogPost, Visitor, ContactMessage, HeroInfo, ContactMethod



@admin.register(TypedRole)
class TypedRoleAdmin(admin.ModelAdmin):
    list_display = ('name',)

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1

@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class')
    inlines = [SkillInline]

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('company', 'role', 'start_date', 'end_date', 'is_present')
    list_filter = ('is_present',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'link')
    ordering = ('number',)

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'degree', 'duration')

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('status', 'created_at')

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'connection_info_type', 'timing', 'created_at')
    list_filter = ('connection_info_type', 'created_at')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(HeroInfo)
class HeroInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'current_company')

@admin.register(ContactMethod)
class ContactMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'link', 'is_full_width', 'order')
    list_editable = ('is_full_width', 'order')


