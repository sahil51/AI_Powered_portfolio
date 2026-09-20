#!/usr/bin/env python
"""
Standalone Runner for resetting and seeding real portfolio data.
Can be executed directly: python seed_real_data.py
"""
import os
import sys

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_project.settings")

import django
django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    print("[*] Invoking portfolio reset command...")
    call_command("reset_portfolio_data")
