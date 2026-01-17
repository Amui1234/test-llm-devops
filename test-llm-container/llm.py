import os
import httpx
from kv import get_openai_api_key

CHAT_URL = os.getenv("AZURE_OPENAI_CHAT_URL")

SYSTEM_PROMPT = (
    "Return ONLY valid JSON with keys: "
    "answer (string), actions (array), follow_up_questions (array of strings). "
    "No markdown. No extra keys."
)

async def chat(messages: list[dict]) -> str:
    api_key = get_openai_api_key()

    payload = {
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"api-key": api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(CHAT_URL, json=payload, headers=headers)

    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
