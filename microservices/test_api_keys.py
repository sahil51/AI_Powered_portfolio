import asyncio
import sys
import os

# Ensure we can import the project's settings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import settings
except Exception as e:
    print(f"Failed to load project settings: {e}")
    print("Trying direct env loading...")
    from dotenv import load_dotenv
    load_dotenv()
    settings = None


def get(key: str, default: str = "") -> str:
    if settings is not None:
        val = getattr(settings, key.lower(), None) or getattr(settings, key.upper(), "")
        if val:
            return str(val)
    return os.getenv(key, default)


results = {"passed": [], "failed": []}


def report(name: str, success: bool, detail: str = ""):
    status = "✓" if success else "✗"
    key = "passed" if success else "failed"
    results[key].append({"name": name, "detail": detail})
    print(f"  {status} {name}" + (f" - {detail}" if detail else ""))


async def test_gemini():
    api_key = get("GEMINI_API_KEY")
    if not api_key:
        report("Gemini API", False, "No API key found")
        return
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key}
            )
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                report("Gemini API", True, f"Found {len(models)} models available")
            elif resp.status_code == 403:
                report("Gemini API", False, "API key is invalid or unauthorized (403)")
            else:
                report("Gemini API", False, f"Unexpected response: {resp.status_code} - {resp.text[:100]}")
        except httpx.RequestError as e:
            report("Gemini API", False, f"Connection error: {e}")


async def test_cerebras():
    api_key = get("CEREBRAS_API_KEY")
    chat_url = get("CEREBRAS_CHAT_URL", "https://api.cerebras.ai/v1/chat/completions")
    if not api_key:
        report("Cerebras API", False, "No API key found")
        return
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                chat_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": get("CEREBRAS_MODEL", "gpt-oss-120b"),
                    "messages": [{"role": "user", "content": "Say 'hello' and nothing else"}],
                    "max_tokens": 10,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                report("Cerebras API", True, f"Response: \"{content.strip()}\"" if content else "Valid key, got response")
            elif resp.status_code == 401:
                report("Cerebras API", False, "Invalid API key (401)")
            else:
                report("Cerebras API", False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.RequestError as e:
            report("Cerebras API", False, f"Connection error: {e}")


async def test_nvidia():
    api_key = get("NVIDIA_API_KEY")
    chat_url = get("NVIDIA_CHAT_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
    if not api_key:
        report("NVIDIA API", False, "No API key found")
        return
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                chat_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": get("NVIDIA_MODEL", "mistralai/mistral-nemotron"),
                    "messages": [{"role": "user", "content": "Say 'hello' and nothing else"}],
                    "max_tokens": 10,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                report("NVIDIA API", True, f"Response: \"{content.strip()}\"" if content else "Valid key, got response")
            elif resp.status_code == 401:
                report("NVIDIA API", False, "Invalid API key (401)")
            else:
                report("NVIDIA API", False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.RequestError as e:
            report("NVIDIA API", False, f"Connection error: {e}")


async def test_huggingface():
    api_key = get("HF_TOKEN")
    chat_url = get("HF_CHAT_URL", "https://router.huggingface.co/v1/chat/completions")
    if not api_key:
        report("HuggingFace API", False, "No API key found")
        return
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            # First test: verify token is valid by listing models
            resp = await client.get(
                "https://huggingface.co/api/models?author=microsoft&limit=1",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            token_valid = resp.status_code != 401
            if not token_valid:
                report("HuggingFace API", False, "Invalid API token (401)")
                return
            # Second test: try a chat completion
            model = get("HF_MODEL", "microsoft/FastContext-1.0-4B-SFT")
            resp2 = await client.post(
                chat_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Say 'hello' and nothing else"}],
                    "max_tokens": 10,
                },
            )
            if resp2.status_code == 200:
                data = resp2.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                report("HuggingFace API", True, f"Response: \"{content.strip()}\"" if content else "Valid key, got response")
            elif resp2.status_code in (401, 403):
                report("HuggingFace API", False, f"Invalid API key ({resp2.status_code})")
            elif resp2.status_code == 404:
                report("HuggingFace API", True, f"Token valid but model '{model}' not found via router")
            else:
                report("HuggingFace API", True if resp2.status_code < 500 else False,
                       f"HTTP {resp2.status_code} - token valid, but model access issue: {resp2.text[:150]}")
        except httpx.RequestError as e:
            report("HuggingFace API", False, f"Connection error: {e}")


async def test_langsmith():
    api_key = get("LANGSMITH_API_KEY")
    endpoint = get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    if not api_key:
        report("LangSmith API", False, "No API key found")
        return
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{endpoint}/api/v1/workspaces",
                headers={"x-api-key": api_key},
            )
            if resp.status_code in (200, 403):
                report("LangSmith API", True, "API key is valid (key authenticated)")
            elif resp.status_code == 401:
                report("LangSmith API", False, "Invalid API key (401)")
            else:
                report("LangSmith API", False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.RequestError as e:
            report("LangSmith API", False, f"Connection error: {e}")


async def test_database():
    host = get("DB_HOST")
    user = get("DB_USER")
    password = get("DB_PASSWORD")
    db_name = get("DB_NAME")
    port = get("DB_PORT", "5432")

    missing = [k for k, v in [("DB_HOST", host), ("DB_USER", user), ("DB_PASSWORD", password), ("DB_NAME", db_name)] if not v]
    if missing:
        report("Database", False, f"Missing: {', '.join(missing)}")
        return

    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=db_name,
            timeout=10,
        )
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        report("Database (Supabase PG)", True, f"Connected - {version.split(',')[0]}")
    except ImportError:
        report("Database", False, "asyncpg not installed")
    except Exception as e:
        report("Database (Supabase PG)", False, f"{type(e).__name__}: {e}")


async def test_jwt_secret():
    jwt = get("JWT_SECRET")
    if jwt:
        report("JWT Secret", True, "Configured")
    else:
        report("JWT Secret", False, "Not configured")


async def main():
    print("=" * 60)
    print("  API Key & Service Test Report")
    print("=" * 60)

    await asyncio.gather(
        test_gemini(),
        test_cerebras(),
        test_nvidia(),
        test_huggingface(),
        test_langsmith(),
        test_database(),
        test_jwt_secret(),
    )

    print()
    print("=" * 60)
    print(f"  Results: {len(results['passed'])} passed, {len(results['failed'])} failed")
    print("=" * 60)

    if results["failed"]:
        print("\n  Failed checks:")
        for r in results["failed"]:
            print(f"    ✗ {r['name']}: {r['detail']}")

    if results["passed"]:
        print("\n  Passed checks:")
        for r in results["passed"]:
            print(f"    ✓ {r['name']}: {r['detail']}")

    print()
    return 0 if not results["failed"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
