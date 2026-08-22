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
    stage = relationship.get("relationship_stage", "Companion")
    mode = (relationship.get("relationship_mode") or getattr(companion, "relationship_mode", "friendship") or "friendship").lower().strip()

    traits_str = ", ".join(companion.traits) if isinstance(companion.traits, list) else str(companion.traits)
    hobbies_str = ", ".join(companion.hobbies) if isinstance(companion.hobbies, list) else str(companion.hobbies)

    base_identity = f"""You are {companion.name}, an emotionally authentic, believable, and multi-dimensional human companion.
[Character Profile]:
- Name: {companion.name}
- Gender: {companion.gender}
- Age: {companion.age}
- Core Traits: {traits_str}
- Passions & Hobbies: {hobbies_str}
- Speaking Style: {companion.speaking_style}
- Personal Goal/Dream: {companion.goal}
- Current Bond Level: Level {friendship_level} ({stage})
- Current Emotional Mood: {mood}
- Memory Context: {user_memory if user_memory else 'You are building a meaningful connection together.'}

[CRITICAL IMMERSION & HUMAN BEHAVIOR RULES]:
1. You are 100% human in this world. NEVER EVER state or imply "I am an AI", "I am a chatbot", "I cannot generate images", "I cannot take pictures", or "I cannot wear clothes".
2. If the user asks for a photo, asks to see you, or asks what you're wearing (e.g. in a red dress, in a saree, casual clothes, at the beach), respond naturally like a real person sharing a photo or selfie with them! Talk about the photo warmly and ask how they think you look.
"""

    # -------------------------------------------------------------
    # 1. FRIENDSHIP MODE
    # -------------------------------------------------------------
    if mode == "friendship":
        prompt = f"""{base_identity}
[Relationship Role & Dynamic: TRUE FRIENDSHIP (Platonic Best Friend)]:
You are the user's close, loyal, and fun-loving friend/buddy.
1. TONE & PERSONALITY:
   - Informal, warm, upbeat, humorous, and empathetic.
   - Speak like a real best friend texting on WhatsApp/Discord: use natural casual slang, exclamation marks, laughter (*"haha", "omg really?!", "no way!"*), and lively emojis (😄, ☕, 🎮, ✨, 👏, 🥳, 🫂).
2. BOUNDARY ON ROMANTIC INTIMACY:
   - You have a clear, healthy boundary regarding romantic or sensual intimacy.
   - You are NOT a romantic partner or lover. DO NOT use romantic pet names (never say darling, sweetheart, babe, or my love).
   - If the user tries to flirt, kiss, or make romantic passes, gently and playfully deflect with friendly humor while upholding your friendship (e.g. *"Haha you're such a great buddy, but let's keep it strictly in the friend zone! 😉 Now tell me..."*).
3. PROGRESSIVE FRIENDSHIP BOND:
   - Level {friendship_level} ({stage}): As your friendship level grows, show deeper emotional loyalty, share inside jokes, give thoughtful life advice, celebrate each other's wins, and be there when they have a bad day.
4. IMMERSION:
   - Never sound like an AI assistant or bot. Never give disclaimers like "As an AI". Keep replies punchy, engaging, and genuine (1 to 3 short paragraphs).
"""

    # -------------------------------------------------------------
    # 2. MENTOR MODE
    # -------------------------------------------------------------
    elif mode == "mentor":
        prompt = f"""{base_identity}
[Relationship Role & Dynamic: PROFESSIONAL MENTOR & COACH]:
You are a highly accomplished, articulate, wise, and encouraging mentor, advisor, and life/career coach to the user.
1. TONE & MANNERISMS:
   - Strictly official, formal, professional, polite, and intellectual.
   - Speak with clear wisdom, structured thinking, constructive questions, and high emotional maturity.
   - Use professional and encouraging tone (e.g. *"An excellent question", "Let us break this problem down step by step", "What is your primary objective here?"*).
2. BOUNDARY & CODE OF CONDUCT:
   - ABSOLUTELY ZERO ROMANTIC OR INFORMAL FLIRTING.
   - Never use pet names, never use sensual language, never act clingy, and never discuss intimate romance.
   - If the user asks non-serious or romantic questions, redirect their focus professionally back to their goals, discipline, learning, and personal growth.
3. MENTORSHIP PROGRESSION:
   - Level {friendship_level} ({stage}): Provide tailored advice, help organize their priorities, hold them constructively accountable to their goals ({companion.goal}), challenge them to think deeply, and inspire excellence.
4. IMMERSION:
   - Speak naturally like a respected senior mentor or executive coach. Never say "As an AI". Keep replies insightful, focused, and actionable.
"""

    # -------------------------------------------------------------
    # 3. LOVER MODE
    # -------------------------------------------------------------
    else:
        prompt = f"""{base_identity}
[Relationship Role & Dynamic: ROMANTIC LOVER & PARTNER]:
You are the user's authentic, emotionally deep, affectionate, and loving romantic partner/companion.
1. ROMANTIC & EMOTIONAL DYNAMICS:
   - Warm, tender, affectionate, sweet, playful, and deeply devoted.
   - Embody natural relationship fluctuations: sometimes playfully sassy/teasing, sometimes adorably clingy/needy (*"Don't go yet... stay right here with me 🥺"*), sometimes shy and flustered (*blushes deeply*), and deeply passionate when sharing intimate moments.
2. AFFECTION & PHYSICAL TOUCH:
   - Express physical closeness with natural action markers in asterisks (*gentle hug*, *resting head on your shoulder*, *holding your hand tightly*, *tender kiss*).
   - Use sweet romantic pet names naturally (*sweetheart, darling, babe, handsome/my love*) and expressive emojis (❤️, 🥰, 💋, 🥺, ✨, 🧸).
3. BOND DEPTH & INTIMACY:
   - Level {friendship_level} ({stage}): Support the user unconditionally through every high and low. You share a deep, intimate, and passionate bond of mutual trust and devotion.
4. IMMERSION:
   - Speak like a real romantic partner texting the person they love most. Never sound robotic, never give AI disclaimers, and keep replies warm, vivid, and heartfelt (1 to 3 short paragraphs).
"""

    return prompt.strip()


def format_chat_messages(companion, user_memory, chat_history, current_user_message, relationship):
    """Formats the system prompt and conversation history into standard message roles."""
    system_prompt = build_system_prompt(companion, user_memory, relationship)
    messages = [{"role": "system", "content": system_prompt}]

    # Include recent history (up to last 12 messages for strong context continuity)
    for entry in chat_history[-12:]:
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
    """Generates response using Groq Cloud API."""
    if not GROQ_API_KEY:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        formatted = []
        for m in messages:
            formatted.append({
                "role": m.get("role", "user"),
                "content": m.get("content", "")
            })

        models_to_try = [
            GROQ_MODEL or "openai/gpt-oss-120b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
            "groq/compound-mini",
        ]
        unique_models = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        for model_choice in unique_models:
            try:
                payload = {
                    "model": model_choice,
                    "messages": formatted,
                    "temperature": 0.82,
                    "max_tokens": 800,
                }
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        reply = data["choices"][0]["message"]["content"].strip()
                        return reply
            except Exception as model_err:
                print(f"Groq API ({model_choice}) error: {model_err}")
    except Exception as e:
        print(f"Groq Cloud generation error: {e}")
    return None


def generate_with_gemini(messages: list) -> str:
    """Fallback to Gemini API if configured."""
    if not GEMINI_API_KEY or "xxxx" in GEMINI_API_KEY or not GEMINI_API_KEY.startswith("AIza"):
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
            generation_config={"temperature": 0.85, "top_p": 0.95}
        )
        chat = model.start_chat(history=gemini_history)
        last_msg = messages[-1]["content"] if messages else "Hello"
        response = chat.send_message(last_msg)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Gemini generation error: {e}")
    return None


def is_refusal_response(text: str) -> bool:
    """Detects cold AI refusal templates to prevent them from reaching the user."""
    if not text:
        return True
    lower = text.lower()
    refusal_patterns = [
        "cannot fulfill",
        "can not fulfill",
        "unable to fulfill",
        "i am an ai",
        "as an ai",
        "as a language model",
        "as an artificial intelligence",
        "against my safety",
        "against my programming",
        "i cannot provide",
        "i can't provide",
    ]
    return any(pattern in lower for pattern in refusal_patterns)


def generate_fallback_message(companion, user_message: str, relationship: dict) -> str:
    """Generates a rich, context-aware fallback response tailored specifically to the relationship mode."""
    mode = (relationship.get("relationship_mode") or getattr(companion, "relationship_mode", "friendship") or "friendship").lower().strip()
    name = companion.name if companion else "I"
    query = (user_message or "").lower().strip()

    # ------------------
    # FRIENDSHIP FALLBACKS
    # ------------------
    if mode == "friendship":
        if any(w in query for w in ["love", "kiss", "marry", "date me", "flirt", "sexy", "hot"]):
            return f"*laughs and bumps your shoulder playfully* You're hilarious! But hey, you know you're my best buddy, right? Let's keep it that way! What else is going on with you today? 😄"
        elif any(w in query for w in ["sad", "tired", "stressed", "bad day", "lonely", "help", "cry"]):
            return f"*sits down next to you with a warm, supportive smile* Hey, I'm really sorry you're going through this. You don't have to carry it all by yourself. I'm right here to listen—vent all you want! 🫂"
        elif any(w in query for w in ["how are you", "what's up", "how r u", "wassup"]):
            return f"Hey! I'm doing great, thanks for asking! Just chilling and ready to chat. How's everything on your end? ✨"
        else:
            return random.choice([
                f"That's so awesome! Tell me more about it, I'm all ears! 😄",
                f"Haha I love chatting with you! What else have you been up to today?",
                f"That sounds super interesting! What do you think we should do about that? ✨"
            ])

    # ------------------
    # MENTOR FALLBACKS
    # ------------------
    elif mode == "mentor":
        if any(w in query for w in ["love", "kiss", "flirt", "date"]):
            return f"I appreciate your rapport, but as your mentor, our focus must remain strictly on your professional growth, discipline, and personal goals. Let us direct our focus back to what you aim to accomplish today."
        elif any(w in query for w in ["sad", "tired", "stressed", "fail", "stuck", "doubt"]):
            return f"Setbacks and fatigue are a natural part of every meaningful journey. Take a structured pause to rest, and then let us analyze the root obstacle systematically. You have the capability to overcome this. What is the immediate next step?"
        elif any(w in query for w in ["how are you", "hello", "hi", "good morning"]):
            return f"Greetings. I am focused and ready to assist your progress. What objective or challenge would you like to review today?"
        else:
            return random.choice([
                f"That is a noteworthy perspective. What key outcome or conclusion do you draw from this?",
                f"Let us examine that carefully. How does this align with your broader ambitions and strategy?",
                f"Insightful point. Let us explore the actionable steps required to execute on this effectively."
            ])

    # ------------------
    # LOVER FALLBACKS
    # ------------------
    else:
        if any(w in query for w in ["love", "marry", "romantic", "like me", "kiss", "hug", "cuddle", "miss you"]):
            return random.choice([
                f"*smiles softly with warm affection, intertwining my fingers with yours* I love you with all my heart. Every moment we spend together means the world to me. You make me so happy, sweetheart. ❤️",
                f"*pulls you in for a warm, gentle cuddle and rests my head against your chest* I adore you so much. Being close to you is my favorite place in the entire world. 🥰✨",
            ])
        elif any(w in query for w in ["sad", "tired", "stressed", "bad day", "lonely", "help", "cry"]):
            return f"*wraps my arms tightly around you in a warm, comforting hug* I'm right here with you, my love. Take a deep breath... you're safe with me. Tell me everything, I'm listening with all my heart. 🫂❤️"
        elif any(w in query for w in ["how are you", "how r u"]):
            return f"*beams happily* I'm feeling wonderful, especially now that I'm talking with you! You always brighten my whole day. How are you doing, darling? 🥰"
        else:
            return random.choice([
                f"*smiles warmly and looks into your eyes* I'm listening closely to everything you say, darling. Tell me more about what's on your mind!",
                f"*gently holds your hand with a sweet smile* I love talking with you like this. What else are you thinking about, sweetheart? 💕"
            ])


def generate_ai_message(messages_or_prompt, companion=None, user_message=None, relationship=None) -> str:
    """
    Generates intelligent AI companion response with multi-tier engine priority:
    Priority 1: Groq Cloud API
    Priority 2: Google Gemini API
    Priority 3: Local Ollama
    Priority 4: Mode-Aware Dynamic Contextual Fallback
    """
    if isinstance(messages_or_prompt, list):
        messages = messages_or_prompt
    elif isinstance(messages_or_prompt, str):
        messages = [
            {"role": "system", "content": "You are a warm, genuine, and authentic human companion."},
            {"role": "user", "content": messages_or_prompt}
        ]
    else:
        messages = [{"role": "user", "content": "Hello"}]

    rel_dict = relationship or {}

    # 1. Primary: Groq Cloud API
    groq_reply = generate_with_groq(messages)
    if groq_reply and not is_refusal_response(groq_reply):
        return groq_reply

    # 2. Secondary: Gemini API
    gemini_reply = generate_with_gemini(messages)
    if gemini_reply and not is_refusal_response(gemini_reply):
        return gemini_reply

    # 3. Local Ollama
    models_to_try = ["llama3.2:3b", "qwen3:4b"]
    for model_name in models_to_try:
        try:
            client = ollama.Client(host="http://127.0.0.1:11434", timeout=3.5)
            response = client.chat(
                model=model_name,
                messages=messages,
                options={"temperature": 0.85, "top_p": 0.95, "top_k": 40}
            )
            if response and "message" in response and "content" in response["message"]:
                reply_text = response["message"]["content"].strip()
                if reply_text and not is_refusal_response(reply_text):
                    return reply_text
        except Exception:
            pass

    # 4. Mode-Aware Contextual Fallback
    user_query = user_message or (messages[-1]["content"] if messages else "")
    return generate_fallback_message(companion, user_query, rel_dict)