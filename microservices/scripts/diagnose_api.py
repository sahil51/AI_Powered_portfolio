import urllib.request
import json

def get_url(url: str):
    try:
        with urllib.request.urlopen(url, timeout=3) as res:
            print(f"URL: {url} -> Status: {res.getcode()}")
            print(res.read().decode("utf-8"))
    except Exception as e:
        print(f"URL: {url} -> Failed: {e}")
        # If HTTPError, print response body
        if hasattr(e, "read"):
            try:
                print(e.read().decode("utf-8"))
            except:
                pass

def main():
    print("=== DIAGNOSING PORT 8000 SERVER ===")
    get_url("http://localhost:8000/health/live")
    get_url("http://localhost:8000/health/ready")
    get_url("http://localhost:8000/health")

if __name__ == "__main__":
    main()
