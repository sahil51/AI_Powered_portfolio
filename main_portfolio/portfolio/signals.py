import threading
import requests
from django.conf import settings
from django.db.models.signals import post_save, post_delete

from portfolio.models import (
    BlogPost,
    ContactMethod,
    Education,
    Experience,
    HeroInfo,
    Project,
    Skill,
    SkillCategory,
)

PORTFOLIO_MODELS = [HeroInfo, Project, Experience, Skill, SkillCategory, Education, BlogPost, ContactMethod]

DEFAULT_REINDEX_URL = "https://ai-portfolio-ai-service.onrender.com/api/reindex"


def _async_post():
    reindex_url = getattr(settings, "REINDEX_WEBHOOK_URL", DEFAULT_REINDEX_URL)
    try:
        resp = requests.post(reindex_url, timeout=30)
        print(f"[Vector Reindex Signal] Live AI Assistant Vector Store Updated: {resp.status_code}")
    except Exception as e:
        print(f"[Vector Reindex Signal] Notice: Could not notify AI Assistant reindex API ({reindex_url}): {e}")


def _trigger_reindex(sender, instance, **kwargs):
    threading.Thread(target=_async_post, daemon=True).start()


for model in PORTFOLIO_MODELS:
    post_save.connect(_trigger_reindex, sender=model, weak=False)
    post_delete.connect(_trigger_reindex, sender=model, weak=False)
