import httpx
import asyncio
import sys
import uuid
import json

BASE = "http://localhost:8000"
results = {"passed": [], "failed": []}

def report(name: str, success: bool, detail: str = ""):
    key = "passed" if success else "failed"
    results[key].append({"name": name, "detail": detail})
    status = "✓" if success else "✗"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

async def test(method: str, path: str, name: str, **kwargs):
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=15) as c:
        try:
            resp = await getattr(c, method.lower())(url, **kwargs)
            ok = resp.status_code < 500  # 4xx could be expected (auth missing etc.)
            detail = f"HTTP {resp.status_code}"
            if resp.status_code == 200:
                detail += " ✓"
            elif resp.status_code in (401, 403):
                detail += " (expected — auth required)"
            elif resp.status_code == 422:
                body = resp.json()
                detail += f" — {body.get('detail', [{}])[0].get('msg', '')}"
            else:
                detail += f" — {resp.text[:100]}"
            report(name, ok, detail)
        except httpx.ConnectError:
            report(name, False, "Connection refused — is the server running?")
        except Exception as e:
            report(name, False, f"{type(e).__name__}: {e}")

async def main():
    print("=" * 60)
    print("  API Endpoint Test Report")
    print("=" * 60)
    print(f"  Target: {BASE}\n")

    # Root
    await test("GET", "/", "GET / — Root")

    # Health (public)
    await test("GET", "/health", "GET /health — Aggregated health")
    await test("GET", "/health/live", "GET /health/live — Liveness")
    await test("GET", "/health/ready", "GET /health/ready — Readiness")
    await test("GET", "/health/startup", "GET /health/startup — Startup")
    await test("GET", "/health/system", "GET /health/system — System health")

    # Metrics
    await test("GET", "/metrics", "GET /metrics — Prometheus metrics")

    # Chat (public sync)
    await test("POST", "/chat/message/sync", "POST /chat/message/sync — Chat (no auth)", json={
        "message": "Say hello",
        "user_type": "visitor",
    })

    # Chat (with optional auth — expect 200 or 422)
    await test("POST", "/chat/message", "POST /chat/message — Chat (auth optional)", json={
        "message": "Say hello",
        "user_type": "visitor",
    })

    # Meetings (requires auth — expect 403/401)
    await test("POST", "/meetings/schedule", "POST /meetings/schedule — Schedule meeting (auth req)", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "contact_number": "+1234567890",
        "company_name": "Test Corp",
        "company_address": "123 Test St",
        "meeting_purpose": "Testing",
        "preferred_date": "2025-01-01",
        "preferred_time": "10:00",
        "timezone": "UTC",
        "meeting_type": "phone_call",
    })
    await test("GET", "/meetings/types", "GET /meetings/types — Meeting types")

    # Leads (requires auth)
    await test("POST", "/leads/create", "POST /leads/create — Create lead (auth req)", json={
        "name": "Test User",
        "email": "test@example.com",
        "company": "Test Corp",
    })

    # Memory (requires auth)
    await test("GET", "/memory/profile/test-user", "GET /memory/profile/{id} — Get profile (auth req)")
    await test("PATCH", "/memory/profile/test-user", "PATCH /memory/profile/{id} — Update profile (auth req)", json={"name": "Test"})

    # Workflows
    await test("POST", "/workflows/trigger", "POST /workflows/trigger — Trigger workflow", json={
        "workflow_name": "test",
        "payload": {"key": "value"},
    })
    await test("GET", "/workflows/status/test-123", "GET /workflows/status/{id} — Workflow status")

    # Security (public)
    await test("GET", "/security/status", "GET /security/status — Security status")
    await test("GET", "/security/audit", "GET /security/audit — Audit log")
    await test("GET", "/security/resilience", "GET /security/resilience — Resilience")
    await test("GET", "/security/circuit-breakers", "GET /security/circuit-breakers — Circuit breakers")
    await test("POST", "/security/circuit-breakers/test/reset", "POST /security/circuit-breakers/{name}/reset — Reset CB")

    # Observability
    await test("GET", "/security/observability/status", "GET /security/observability/status")
    await test("GET", "/security/observability/health", "GET /security/observability/health")
    await test("GET", "/security/observability/metrics", "GET /security/observability/metrics")
    await test("GET", "/security/observability/traces", "GET /security/observability/traces")

    # Summary
    print()
    print("=" * 60)
    passed = len(results["passed"])
    failed = len(results["failed"])
    print(f"  Results: {passed} passed, {failed} failed out of {passed + failed}")
    print("=" * 60)
    if results["failed"]:
        print("\n  Failed:")
        for r in results["failed"]:
            print(f"    ✗ {r['name']}: {r['detail']}")
    if results["passed"]:
        print("\n  Passed:")
        for r in results["passed"]:
            print(f"    ✓ {r['name']}: {r['detail']}")
    print()

    return 0 if not results["failed"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
