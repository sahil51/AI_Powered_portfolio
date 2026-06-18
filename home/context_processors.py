from .models import Profile

def profile_context(request):
    """
    Globally provides the 'profile' object to all templates
    so the navbar and footer can render correctly on every page.
    """
    return {
        'profile': Profile.objects.first()
    }
