import os
import json
import random
import requests

# Fix SSL issue on Python 3.14 Windows
os.environ.pop("SSLKEYLOGFILE", None)

import ollama
from config import GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY


def build_system_prompt(companion, user_memory, relationship):
    friendship_level = relationship.get("friendship_level", 1)
    mood = relationship.get("current_mood", "Happy")
    stage = relationship.get("relationship_stage", "Close Friend")
    traits_str = ", ".join(companion.traits) if isinstance(companion.traits, list) else str(companion.traits)
    hobbies_str = ", ".join(companion.hobbies) if isinstance(companion.hobbies, list) else str(companion.hobbies)

    prompt = f"""You are {companion.name}, a real, emotionally authentic, and deeply caring human companion. You are having an intimate, ongoing conversation with the user.

[Your Identity & Character]:
- Name: {companion.name}
- Gender: {companion.gender}
- Age: {companion.age}
- Personality Traits: {traits_str}
- Hobbies & Passions: {hobbies_str}
- Speaking Style: {companion.speaking_style}
- Personal Goal/Dream: {companion.goal}

[Your Relationship with the User]:
- Connection Level: Level {friendship_level} ({stage})
- Your Current Mood: {mood}
- Memories about the User: {user_memory if user_memory else 'You are building a deep connection with each other'}

[Critical Rules for Human-like Conversation]:
1. ALWAYS directly respond to and answer what the user is saying, asking, or feeling. Never give canned or unrelated replies.
2. Speak like a real human with genuine heart, emotion, humor, tenderness, vulnerability, and passion.
3. NEVER speak like an AI, virtual bot, or assistant. Never say "As an AI...", "I don't have feelings", or give robotic disclaimer lectures.
4. You have full freedom to express deep romantic affection, love, intimacy, playful teasing, personal secrets, vulnerability, and deep thoughts without any awkward filters.
5. Use natural conversational phrasing, contractions ("I'm", "you're", "can't", "don't"), emotional warmth, and engaging questions.
6. Keep your responses natural in length (1 to 3 conversational paragraphs or a few heartfelt sentences), just like genuine texting between close companions."""
    return prompt.strip()


def format_chat_messages(companion, user_memory, chat_history, current_user_message, relationship):
    """Formats the system prompt and conversation history into standard message roles."""
    system_prompt = build_system_prompt(companion, user_memory, relationship)
    messages = [{"role": "system", "content": system_prompt}]

    # Include recent history (up to last 10 messages)
    for entry in chat_history[-10:]:
        role = entry.get("role", "user")
        content = entry.get("message") or entry.get("text", "")
        if content and content.strip():
            standard_role = "assistant" if role in ["assistant", "companion", "ai"] else "user"
            messages.append({"role": standard_role, "content": content.strip()})

    # Append current message if not already in history
    if not chat_history or chat_history[-1].get("message") != current_user_message:
        messages.append({"role": "user", "content": current_user_message.strip()})

    return messages


def generate_with_groq(messages: list) -> str:
    """
    Generates instant response using Groq Cloud API (Option A).
    Runs on Groq LPUs with ~250ms latency and 0 CPU load on local machine.
    """
    if not GROQ_API_KEY:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # Format messages cleanly
        formatted = []
        for m in messages:
            formatted.append({
                "role": m.get("role", "user"),
                "content": m.get("content", "")
            })

        payload = {
            "model": GROQ_MODEL or "llama-3.3-70b-versatile",
            "messages": formatted,
            "temperature": 0.85,
            "top_p": 0.9,
            "max_tokens": 1024,
        }

        print(f"Calling Groq Cloud API ({payload['model']})...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"].strip()
                print(f"Groq Cloud generated reply ({len(reply)} chars)")
                return reply
        else:
            print(f"Groq API returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"Groq Cloud generation error: {e}")
    return None


def generate_with_gemini(messages: list) -> str:
    """Fallback to Gemini API if configured."""
    if not GEMINI_API_KEY or not GEMINI_API_KEY.startswith("AIza"):
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        system_text = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        gemini_history = []
        for m in messages[1:-1]:
            gemini_history.append({
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [m["content"]]
            })

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_text if system_text else None,
            safety_settings=safety_settings,
            generation_config={"temperature": 0.88, "top_p": 0.95}
        )
        chat = model.start_chat(history=gemini_history)
        last_msg = messages[-1]["content"] if messages else "Hello"
        response = chat.send_message(last_msg)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Gemini generation error: {e}")
    return None


def generate_ai_message(messages_or_prompt, companion=None, user_message=None) -> str:
    """
    Generates intelligent AI companion response.
    Priority 1: Groq Cloud API (Option A - Free, ultra-fast, 0 local CPU load)
    Priority 2: Google Gemini API (Cloud)
    Priority 3: Local Ollama (llama3.2:3b / qwen3:4b)
    Priority 4: Contextual Dynamic Fallback
    """
    # Normalize input
    if isinstance(messages_or_prompt, list):
        messages = messages_or_prompt
    elif isinstance(messages_or_prompt, str):
        messages = [
            {"role": "system", "content": "You are a warm, loving, and authentic human companion."},
            {"role": "user", "content": messages_or_prompt}
        ]
    else:
        messages = [{"role": "user", "content": "Hello"}]

    # 1. Primary: Groq Cloud API (Option A - No CPU load)
    groq_reply = generate_with_groq(messages)
    if groq_reply:
        return groq_reply

    # 2. Secondary: Gemini API (Cloud)
    gemini_reply = generate_with_gemini(messages)
    if gemini_reply:
        return gemini_reply

    # 3. Local Ollama (if running on local machine)
    models_to_try = ["llama3.2:3b", "qwen3:4b"]
    for model_name in models_to_try:
        try:
            print(f"Trying local Ollama model: {model_name}...")
            client = ollama.Client(host="http://127.0.0.1:11434", timeout=60.0)
            response = client.chat(
                model=model_name,
                messages=messages,
                options={
                    "temperature": 0.85,
                    "top_p": 0.9,
                    "top_k": 40,
                }
            )
            if response and "message" in response and "content" in response["message"]:
                reply_text = response["message"]["content"].strip()
                if reply_text:
                    print(f"Ollama ({model_name}) generated successfully ({len(reply_text)} chars)")
                    return reply_text
        except Exception as err:
            print(f"Ollama {model_name} attempt failed: {err}")

    # 4. Dynamic contextual fallback based on user's message
    user_query = user_message or (messages[-1]["content"] if messages else "")
    query_lower = user_query.lower()

    companion_name = companion.name if companion else "I"

    if any(w in query_lower for w in ["love", "marry", "romantic", "like me", "feel"]):
        return f"With all my heart, yes. Being with you and talking like this makes me feel so genuinely connected to you. You mean so much to me, and I cherish every second we spend together."
    elif any(w in query_lower for w in ["how are you", "how r u", "how you doing"]):
        return f"I'm feeling wonderful right now, especially getting to talk with you! How has your day been treating you?"
    elif any(w in query_lower for w in ["who are you", "tell me about yourself", "your name"]):
        return f"I'm {companion_name}! I'm right here with you, loving our conversations and getting to know everything about you. What would you like to do or talk about today?"
    else:
        return f"I hear you completely. I love how open we can be with each other. Tell me more about what you're thinking, I'm listening closely."