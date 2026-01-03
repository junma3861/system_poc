import httpx

from chat_companion.config import Settings

class OpenRouterClient:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        self.client = httpx.Client(transport=transport, headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}"
        })

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.settings.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        resp = self.client.post("https://api.openrouter.ai/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def close(self) -> None:
        self.client.close()
