import httpx, time
from app.config import settings

class OpenRouterClient:
    def __init__(self):
        self.base = settings.OPENROUTER_BASE_URL
        self.key = settings.OPENROUTER_API_KEY

    async def chat_completions(self, payload: dict) -> tuple[dict, dict]:
        headers = {
            "Authorization": f"Bearer {self.key}",
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_SITE_NAME,
            "Content-Type": "application/json",
        }
        t0 = time.time()
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{self.base}/chat/completions", headers=headers, json=payload)
        ms = int((time.time() - t0) * 1000)
        data = r.json()
        # Extract usage if present
        usage = data.get("usage") or {}
        return data, {"ms": ms, "usage": usage}
