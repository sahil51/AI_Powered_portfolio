import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
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
            
            # Send Email Notification
            try:
                recipient = getattr(settings, 'NOTIFICATION_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')
                if recipient and recipient.strip():
                    subject = f"New Portfolio Contact Message from {name}"
                    text_body = f"You received a new message on your portfolio:\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message_text}\n\n--- Sent from AI Portfolio Contact Form ---"
                    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>New Contact Message</title></head>
<body style="margin: 0; padding: 0; background-color: #0a0f1d; font-family: 'Segoe UI', Roboto, sans-serif; color: #e2e8f0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0a0f1d; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 600px; background-color: #141c2e; border: 1px solid rgba(0, 242, 254, 0.25); border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" cellspacing="0" cellpadding="0" border="0">
          <tr>
            <td style="background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); padding: 22px 30px;">
              <h1 style="margin: 0; font-size: 20px; font-weight: 800; color: #0a0f1d; text-transform: uppercase; letter-spacing: 1px;">NEW CONTACT FORM MESSAGE</h1>
              <p style="margin: 3px 0 0 0; font-size: 12px; color: #0a0f1d; font-weight: 700;">SAHIL THAKUR | PORTFOLIO</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 28px 30px;">
              <h2 style="margin: 0 0 14px 0; font-size: 20px; font-weight: 700; color: #ffffff;">Message Details</h2>
              <table role="presentation" width="100%" style="background-color: #0b1120; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 18px 20px; margin-bottom: 20px;">
                <tr>
                  <td style="padding: 10px 0; border-bottom: 1px dashed rgba(255,255,255,0.08); font-size: 14px; color: #94a3b8; width: 30%; font-weight: 600;">Sender Name</td>
                  <td style="padding: 10px 0; border-bottom: 1px dashed rgba(255,255,255,0.08); font-size: 14px; color: #ffffff; font-weight: 500;">{name}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 0; border-bottom: 1px dashed rgba(255,255,255,0.08); font-size: 14px; color: #94a3b8; font-weight: 600;">Sender Email</td>
                  <td style="padding: 10px 0; border-bottom: 1px dashed rgba(255,255,255,0.08); font-size: 14px; color: #00f2fe; font-weight: 500;"><a href="mailto:{email}" style="color:#00f2fe;">{email}</a></td>
                </tr>
                <tr>
                  <td style="padding: 10px 0; font-size: 14px; color: #94a3b8; font-weight: 600; vertical-align: top;">Message</td>
                  <td style="padding: 10px 0; font-size: 14px; color: #cbd5e1; font-weight: 400; line-height: 1.5;">{message_text}</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background-color: #0d1424; padding: 18px 30px; border-top: 1px solid rgba(255,255,255,0.06); text-align: center;">
              <p style="margin: 0; font-size: 12px; color: #64748b;">Sent automatically by <strong style="color: #00f2fe;">Sahil Thakur's Portfolio Contact Form</strong></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
                    send_mail(
                        subject=subject,
                        message=text_body,
                        html_message=html_body,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or recipient,
                        recipient_list=[recipient],
                        fail_silently=True,
                    )
            except Exception as e:
                print(f"[Contact Form Email] Error sending email: {e}")

            messages.success(request, "Your message has been sent successfully!")
        else:
            messages.error(request, "Please fill in all fields.")
            
    return redirect('portfolio:home')


from django.utils.text import slugify

@csrf_exempt
def api_create_blog_post(request):
    """
    Webhook API Endpoint for n8n / Telegram automation.
    Accepts JSON payload to create and publish blog posts automatically.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)

    # Secret API Key verification
    api_key_header = request.headers.get('X-Blog-API-Key') or request.META.get('HTTP_X_BLOG_API_KEY')
    expected_key = getattr(settings, 'BLOG_WEBHOOK_SECRET_KEY', 'sahil_blog_secret_2026_key')

    if api_key_header != expected_key:
        return JsonResponse({'error': 'Unauthorized. Invalid or missing X-Blog-API-Key.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    title = data.get('title', '').strip()
    summary = data.get('summary', '').strip()
    content = data.get('content', '').strip()
    status_val = data.get('status', 'Published').strip()
    custom_slug = data.get('slug', '').strip()

    if not title or not content:
        return JsonResponse({'error': 'Missing required fields: title and content are required.'}, status=400)

    if not summary:
        import re
        clean_text = re.sub('<[^<]+?>', '', content)
        summary = clean_text[:180] + '...' if len(clean_text) > 180 else clean_text

    base_slug = slugify(custom_slug or title) or 'blog-post'
    slug = base_slug
    counter = 1
    while BlogPost.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    blog = BlogPost.objects.create(
        title=title,
        slug=slug,
        summary=summary,
        content=content,
        status=status_val if status_val in ['Published', 'Draft'] else 'Published'
    )

    return JsonResponse({
        'success': True,
        'message': 'Blog post created and published successfully!',
        'id': blog.id,
        'title': blog.title,
        'slug': blog.slug,
        'status': blog.status,
        'created_at': blog.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'url': f'/blog/{blog.slug}/'
    }, status=201)


