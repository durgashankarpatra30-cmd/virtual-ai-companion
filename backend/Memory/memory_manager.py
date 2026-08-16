import json
import re
import requests
from config import GROQ_API_KEY, GROQ_MODEL

# Patterns that indicate genuine user facts/preferences, avoiding false matches on conversational questions like "do you love me"
FACT_PATTERNS = [
    r"\bmy favorite\b",
    r"\bi (really )?(love|like|enjoy|prefer|hate|dislike)\s+(?!you\b)",
    r"\bmy (goal|dream|birthday|job|college|hobby|family|pet|dog|cat|name)\b",
    r"\bi (work as|live in|am from|study at)\b",
    r"\bi'm (a|an)\s+\w+",
]

def should_save_memory(message):
    message = message.lower()
    for pattern in FACT_PATTERNS:
        if re.search(pattern, message):
            return True
    return False

def extract_memory(user_message):
    prompt = f"""You are a JSON-only extraction engine.
Extract any key long-term facts or personal preferences about the user from their message.
Return ONLY valid JSON dictionary with concise keys and values.
If there are no personal facts, return {{}}.

Examples:
Input: My birthday is 21st December
Output: {{"birthday": "21st December"}}

Input: I love pizza and my dog's name is Milo
Output: {{"favorite_food": "pizza", "pet_name": "Milo"}}

Input: Hello my love
Output: {{}}

User message: {user_message}"""

    # 1. Try Groq Cloud API first if available
    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama-3.1-8b-instant" if "llama-3.1-8b-instant" in (GROQ_MODEL or "") else (GROQ_MODEL or "llama-3.3-70b-versatile"),
                "messages": [
                    {"role": "system", "content": "You are a JSON fact extractor. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 200,
            }
            res = requests.post(url, headers=headers, json=payload, timeout=4)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"].strip()
                content = re.sub(r"```json|```", "", content).strip()
                memory = json.loads(content)
                if isinstance(memory, dict):
                    return memory
        except Exception as e:
            print(f"Groq memory extraction notice: {e}")

    # 2. Try Ollama if running (with 3s timeout)
    try:
        import ollama
        client = ollama.Client(host="http://127.0.0.1:11434", timeout=3.0)
        response = client.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1}
        )
        response_text = response["message"]["content"]
        response_text = re.sub(r"```json|```", "", response_text).strip()
        memory = json.loads(response_text)
        if isinstance(memory, dict):
            return memory
    except Exception:
        pass

    return {}
