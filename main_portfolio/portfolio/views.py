import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import TypedRole, SkillCategory, Skill, Experience, Project, Education, BlogPost, Visitor, ContactMessage, HeroInfo

def home_view(request):
    hero = HeroInfo.objects.first()
    if not hero:
        hero = HeroInfo.objects.create()

    roles = [role.name for role in TypedRole.objects.all()]
    # Fallback default if DB is empty
    if not roles:
        roles = ["Backend Engineer", "AI Engineer", "Full Stack Developer"]
        
    skill_categories = SkillCategory.objects.prefetch_related('skills').all()
    experiences = Experience.objects.all().order_by('-start_date')  # Sort appropriately
    projects = Project.objects.all().order_by('number')
    educations = Education.objects.all()
    
    # Get latest blogs for homepage display if needed (e.g. latest 3)
    latest_blogs = BlogPost.objects.filter(status='Published').order_by('-created_at')[:3]
    
    context = {
        'hero': hero,
        'roles': roles,
        'skill_categories': skill_categories,
        'experiences': experiences,
        'projects': projects,
        'educations': educations,
        'latest_blogs': latest_blogs,
    }
    return render(request, 'portfolio/index.html', context)


def blog_list_view(request):
    blogs = BlogPost.objects.filter(status='Published').order_by('-created_at')
    return render(request, 'portfolio/blog.html', {'blogs': blogs})

def blog_detail_view(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug, status='Published')
    return render(request, 'portfolio/blog_detail.html', {'blog': blog})

def visitors_view(request):
    visitors = Visitor.objects.all().order_by('-created_at')
    return render(request, 'portfolio/visitors.html', {'visitors': visitors})

def contact_submit_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        if name and email and message_text:
            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message_text
            )
            messages.success(request, "Your message has been sent successfully!")
        else:
            messages.error(request, "Please fill in all fields.")
            
    return redirect('portfolio:home')


