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

MICROSERVICE_URL = getattr(settings, "REINDEX_WEBHOOK_URL", "http://127.0.0.1:8001/api/reindex")


def _async_post():
    try:
        resp = requests.post(MICROSERVICE_URL, timeout=10)
        print(f"[Vector Reindex Signal] AI Assistant Vector Store Updated automatically: {resp.status_code}")
    except Exception as e:
        print(f"[Vector Reindex Signal] Notice: Could not notify AI Assistant reindex API: {e}")


def _trigger_reindex(sender, instance, **kwargs):
    threading.Thread(target=_async_post, daemon=True).start()


for model in PORTFOLIO_MODELS:
    post_save.connect(_trigger_reindex, sender=model, weak=False)
    post_delete.connect(_trigger_reindex, sender=model, weak=False)
