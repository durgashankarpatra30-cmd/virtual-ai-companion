import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

COMPANION_FILE = os.path.join(DATA_DIR, "companion.json")
USER_MEMORY_FILE = os.path.join(DATA_DIR, "user_memory.json")
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")
RELATIONSHIP_FILE = os.path.join(DATA_DIR, "relationship.json")


def save_companion(companion):
    data = {
        "name": companion.name,
        "gender": getattr(companion, "gender", "Female"),
        "age": companion.age,
        "traits": companion.traits,
        "hobbies": companion.hobbies,
        "speaking_style": companion.speaking_style,
        "goal": companion.goal,
        "voice_id": getattr(companion, "voice_id", "en-US-AriaNeural"),
        "voice_speed": getattr(companion, "voice_speed", "+0%"),
        "voice_pitch": getattr(companion, "voice_pitch", "+0Hz"),
    }
    with open(COMPANION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return data


def load_companion():
    if not os.path.exists(COMPANION_FILE):
        return None
    try:
        with open(COMPANION_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except Exception:
        return None


def save_user_memory(memory):
    with open(USER_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)


def load_user_memory():
    if not os.path.exists(USER_MEMORY_FILE):
        return {}
    try:
        with open(USER_MEMORY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception:
        return {}


def load_chat_history():
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception:
        return []


def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def load_relationship():
    default_rel = {
        "friendship_level": 1,
        "days_talked": 1,
        "total_messages": 0,
        "favorite_topics": [],
        "current_mood": "Happy",
        "relationship_progress": 0,
        "relationship_stage": "New Acquaintance",
    }
    if not os.path.exists(RELATIONSHIP_FILE):
        return default_rel
    try:
        with open(RELATIONSHIP_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default_rel
            return json.loads(content)
    except Exception:
        return default_rel


def save_relationship(data):
    with open(RELATIONSHIP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def reset_companion_data():
    """Reset chat history, user memory, and relationship for a fresh companion."""
    save_chat_history([])
    save_user_memory({})
    initial_relationship = {
        "friendship_level": 1,
        "days_talked": 1,
        "total_messages": 0,
        "favorite_topics": [],
        "current_mood": "Happy",
        "relationship_progress": 0,
        "relationship_stage": "New Acquaintance",
    }
    save_relationship(initial_relationship)
    return initial_relationship