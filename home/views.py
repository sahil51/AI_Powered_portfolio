import json
import uuid
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Profile, TypedRole, SocialLink, Stat,
    SkillCategory, Experience, Project,
    Education, ContactItem, Blog, WhatsAppChat
)
from .ai_agents import RecruiterAgent
from .twilio_utils import notify_user_via_whatsapp



def index(request):
    """Render the portfolio homepage with all dynamic data from DB."""
    typed_roles = list(TypedRole.objects.values_list("title", flat=True))
    social_links = SocialLink.objects.all()
    stats = Stat.objects.all()
    skill_categories = SkillCategory.objects.prefetch_related("skills").all()
    experiences = Experience.objects.prefetch_related("projects", "achievements", "techs").all()
    projects = Project.objects.prefetch_related("techs").all()
    educations = Education.objects.prefetch_related("scores").all()
    contact_items = ContactItem.objects.all()
    blogs = Blog.objects.prefetch_related("tags").filter(is_published=True, is_featured=True).order_by("order", "-published_date")[:3]

    context = {
        "typed_roles_json": json.dumps(typed_roles),
        "social_links": social_links,
        "stats": stats,
        "skill_categories": skill_categories,
        "experiences": experiences,
        "projects": projects,
        "educations": educations,
        "blogs": blogs,
        "contact_items": contact_items,
    }
    return render(request, "index.html", context)


def blog_list(request):
    """Render all published blogs."""
    blogs = Blog.objects.prefetch_related("tags").filter(is_published=True).order_by("-published_date")
    return render(request, "blog_list.html", {"blogs": blogs})


def blog_detail(request, slug):
    """Render a single blog detail page."""
    blog = get_object_or_404(Blog, slug=slug, is_published=True)
    return render(request, "blog_detail.html", {"blog": blog})


@csrf_exempt
def whatsapp_webhook(request):
    """
    Webhook endpoint for Twilio incoming WhatsApp messages.
    """
    if request.method == "POST":
        incoming_msg = request.POST.get("Body", "").strip()
        sender = request.POST.get("From", "")
        
        if not incoming_msg or not sender:
            return HttpResponse("Invalid request", status=400)
            
        # Get or create chat session
        chat, created = WhatsAppChat.objects.get_or_create(phone_number=sender)
        history = chat.history if isinstance(chat.history, list) else json.loads(chat.history or "[]")
        
        # Initialize agent
        agent = RecruiterAgent(phone_number=sender, request=request)
        
        # Get AI response
        ai_response = agent.process_message(incoming_msg, history)
        
        # Update history
        history.append({"role": "user", "content": incoming_msg})
        history.append({"role": "ai", "content": ai_response})
        chat.history = history
        chat.save()
        
        # Twilio requires TwiML or we can just send via API
        # Using TwiML is faster for direct response
        from twilio.twiml.messaging_response import MessagingResponse
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(ai_response)
        
        # Notify the portfolio owner about the interaction
        if created or "resume" in incoming_msg.lower() or "interview" in incoming_msg.lower():
            notify_user_via_whatsapp(f"New interaction from {sender}:\n\nUser: {incoming_msg}\n\nAI: {ai_response}")
            
        return HttpResponse(str(resp), content_type="text/xml")
        
    return HttpResponse("Method not allowed", status=405)


@csrf_exempt
def web_chat(request):
    """
    Endpoint for the frontend AI chat widget.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            incoming_msg = data.get("message", "").strip()
            session_id = data.get("session_id", "")
            
            if not session_id:
                session_id = f"web_{uuid.uuid4().hex[:10]}"
                
            if not incoming_msg:
                return JsonResponse({"error": "No message provided"}, status=400)
                
            # Get or create chat session
            chat, created = WhatsAppChat.objects.get_or_create(phone_number=session_id)
            history = chat.history if isinstance(chat.history, list) else json.loads(chat.history or "[]")
            
            # Initialize agent
            agent = RecruiterAgent(phone_number=session_id, request=request)
            
            # Get AI response
            ai_response = agent.process_message(incoming_msg, history)
            
            # Update history
            history.append({"role": "user", "content": incoming_msg})
            history.append({"role": "ai", "content": ai_response})
            chat.history = history
            chat.save()
            
            # Notify the portfolio owner about the interaction
            if created or "resume" in incoming_msg.lower() or "interview" in incoming_msg.lower():
                notify_user_via_whatsapp(f"New Web Chat interaction (ID: {session_id}):\n\nUser: {incoming_msg}\n\nAI: {ai_response}")
                
            return JsonResponse({"response": ai_response, "session_id": session_id})
        except Exception as e:
            import traceback
            traceback.print_exc()  # prints full error in terminal
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)

