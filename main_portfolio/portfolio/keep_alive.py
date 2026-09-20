import os
import time
import threading
import requests
from django.conf import settings

_started = False
_lock = threading.Lock()


def _keep_alive_loop():
    # Wait 25 seconds after server boot to allow full initialization
    time.sleep(25)

    # Ping interval: default 300 seconds (5 minutes) to comfortably beat Render's 15-minute inactivity timer
    interval = int(os.getenv("KEEP_ALIVE_INTERVAL_SECONDS", "300"))

    while True:
        try:
            # 1. Self-ping Django Portfolio via Render's public URL
            render_url = os.getenv("RENDER_EXTERNAL_URL") or getattr(settings, "PORTFOLIO_URL", "")
            if render_url:
                target_url = render_url.rstrip("/") + "/health/"
                try:
                    resp = requests.get(target_url, timeout=15)
                    print(f"[Keep-Alive] Self-pinged {target_url} -> Status {resp.status_code}")
                except Exception as e:
                    print(f"[Keep-Alive] Self-ping notice ({target_url}): {e}")

            # 2. Also keep the live AI Assistant Microservice awake on Render
            ai_url = getattr(settings, "AI_SERVICE_URL", "").rstrip("/")
            if ai_url and "onrender.com" in ai_url:
                ai_health_url = f"{ai_url}/health"
                try:
                    resp_ai = requests.get(ai_health_url, timeout=15)
                    print(f"[Keep-Alive] AI Assistant pinged {ai_health_url} -> Status {resp_ai.status_code}")
                except Exception as e:
                    print(f"[Keep-Alive] AI Assistant ping notice ({ai_health_url}): {e}")

        except Exception as err:
            print(f"[Keep-Alive] Error during keep-alive cycle: {err}")

        time.sleep(interval)


def start_keep_alive():
    """Initializes the background keep-alive daemon thread once per process."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    # Only run in production or when explicitly enabled
    is_prod = not getattr(settings, "DEBUG", True)
    explicit_enable = os.getenv("ENABLE_KEEP_ALIVE", "").lower() in ("true", "1", "yes")

    if is_prod or explicit_enable or os.getenv("RENDER_EXTERNAL_URL"):
        thread = threading.Thread(target=_keep_alive_loop, daemon=True, name="RenderKeepAliveDaemon")
        thread.start()
        print("[Keep-Alive] Auto-pinger daemon thread started (every 5 minutes)")
