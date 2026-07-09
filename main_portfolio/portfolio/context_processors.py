from django.conf import settings
from .models import HeroInfo, ContactMethod

def hero_context(request):
    """
    Makes the HeroInfo and ContactMethod objects globally accessible in all templates.
    """
    try:
        hero = HeroInfo.objects.first()
        if not hero:
            hero = HeroInfo.objects.create()
        contact_methods = ContactMethod.objects.all().order_by('order')
    except Exception:
        hero = None
        contact_methods = []
    return {
        'hero': hero,
        'contact_methods': contact_methods,
        'chat_api_url': getattr(settings, 'CHAT_API_URL', '/api/chat/'),
    }

