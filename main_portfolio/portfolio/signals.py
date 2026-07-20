import requests

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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


def _trigger_reindex(sender, instance, **kwargs):
    try:
        requests.post(MICROSERVICE_URL, timeout=5)
    except requests.RequestException:
        pass


for model in PORTFOLIO_MODELS:
    post_save.connect(_trigger_reindex, sender=model, weak=False)
    post_delete.connect(_trigger_reindex, sender=model, weak=False)
