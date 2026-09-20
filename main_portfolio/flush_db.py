import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_project.settings")

import django
django.setup()

from django.db import connection
from portfolio.models import (
    HeroInfo, TypedRole, SkillCategory, Skill, Experience,
    Project, Education, BlogPost, Visitor, ContactMessage, ContactMethod
)

print("[*] Flushing all portfolio tables...")

models = [
    ContactMessage,
    Visitor,
    Project,
    BlogPost,
    Experience,
    Skill,
    SkillCategory,
    TypedRole,
    ContactMethod,
    HeroInfo,
]

total_deleted = 0
for m in models:
    count, _ = m.objects.all().delete()
    total_deleted += count
    print(f"  - Deleted {count} records from {m.__name__}")

# Also check raw SQL for any orphaned tables like meeting_requests, chat_messages if they exist
with connection.cursor() as cursor:
    for extra_tbl in ['meeting_requests', 'chat_messages', 'portfolio_visitor']:
        try:
            cursor.execute(f"DELETE FROM {extra_tbl};")
            print(f"  - Flushed raw table '{extra_tbl}' (rows affected: {cursor.rowcount})")
        except Exception as e:
            # Table might not exist or already empty
            pass

print(f"\n[✓] DATABASE FLUSH COMPLETED! Total records removed: {total_deleted}")

# Verify row counts
print("\n[*] Verifying zero records:")
for m in models:
    print(f"  - {m.__name__}: {m.objects.count()} records")
