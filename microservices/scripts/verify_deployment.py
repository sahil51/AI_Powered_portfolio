import sys
import urllib.request


def verify_endpoint(url: str, name: str) -> bool:
    print(f"Checking {name} endpoint at: {url} ...")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            if status == 200:
                print(f"[SUCCESS] {name} is operational. Response: {body[:150]}")
                return True
            else:
                print(f"[FAILURE] {name} returned status code: {status}")
                return False
    except Exception as e:
        print(f"[FAILURE] Connection to {name} failed: {e}")
        return False

def main():
    base_url = "http://localhost:8000"

    health_live = verify_endpoint(f"{base_url}/health/live", "Liveness Check")
    health_ready = verify_endpoint(f"{base_url}/health/ready", "Readiness Check")
    health_full = verify_endpoint(f"{base_url}/health", "Full Health Check")

    # Check Prometheus Metrics endpoint (which runs on port 8000 or the custom configured port)
    # The default /metrics route is usually registered or exposed.
    # In fastapi app, we can also check / if operational.
    root_check = verify_endpoint(f"{base_url}/", "Root Endpoint Check")

    if health_live and health_ready and health_full and root_check:
        print("\n=== [DEPLOYMENT SUCCESSFUL] All systems validated successfully! ===")
        sys.exit(0)
    else:
        print("\n=== [DEPLOYMENT FAILED] One or more health checks failed! ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
