import json
import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
os.makedirs(USERS_DIR, exist_ok=True)


def sanitize_user_id(user_id: str) -> str:
    """Sanitizes user ID to prevent path traversal and ensure valid directory naming."""
    if not user_id or not isinstance(user_id, str):
        return "default_user"
    clean = re.sub(r"[^a-zA-Z0-9_-]", "", user_id.strip())
    return clean if clean else "default_user"


def get_user_dir(user_id: str = "default_user") -> str:
    """Gets or creates the isolated directory for a specific user."""
    clean_id = sanitize_user_id(user_id)
    user_path = os.path.join(USERS_DIR, clean_id)
    os.makedirs(user_path, exist_ok=True)
    return user_path


def _migrate_legacy_data_if_needed():
    """Migrates any root legacy data into data/users/default_user if needed."""
    try:
        default_dir = os.path.join(USERS_DIR, "default_user")
        legacy_companion = os.path.join(DATA_DIR, "companion.json")
        if os.path.exists(legacy_companion) and not os.path.exists(os.path.join(default_dir, "companion.json")):
            os.makedirs(default_dir, exist_ok=True)
            for fname in ["companion.json", "user_memory.json", "chat_history.json", "relationship.json"]:
                src = os.path.join(DATA_DIR, fname)
                dst = os.path.join(default_dir, fname)
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
    except Exception as e:
        print(f"Legacy data migration note: {e}")


# Run migration check on startup
_migrate_legacy_data_if_needed()


def get_companion_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "companion.json")


def get_user_memory_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "user_memory.json")


def get_chat_history_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "chat_history.json")


def get_relationship_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "relationship.json")


def save_companion(companion, user_id: str = "default_user"):
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
        "relationship_mode": getattr(companion, "relationship_mode", "friendship") or "friendship",
    }
    file_path = get_companion_file(user_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return data


def load_companion(user_id: str = "default_user"):
    file_path = get_companion_file(user_id)
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except Exception:
        return None


def save_user_memory(memory, user_id: str = "default_user"):
    file_path = get_user_memory_file(user_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)


def load_user_memory(user_id: str = "default_user"):
    file_path = get_user_memory_file(user_id)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception:
        return {}


def load_chat_history(user_id: str = "default_user"):
    file_path = get_chat_history_file(user_id)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception:
        return []


def save_chat_history(history, user_id: str = "default_user"):
    file_path = get_chat_history_file(user_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def get_default_relationship(mode: str = "friendship"):
    mode = mode or "friendship"
    if mode == "mentor":
        stage = "New Mentee"
    elif mode == "lover":
        stage = "Sweet Spark"
    else:
        stage = "New Acquaintance"

    return {
        "friendship_level": 1,
        "days_talked": 1,
        "total_messages": 0,
        "favorite_topics": [],
        "current_mood": "Happy",
        "relationship_progress": 0,
        "relationship_stage": stage,
        "relationship_mode": mode,
    }


def load_relationship(user_id: str = "default_user", mode: str = None):
    file_path = get_relationship_file(user_id)
    companion = load_companion(user_id)
    active_mode = mode or (companion.get("relationship_mode") if companion else "friendship") or "friendship"
    default_rel = get_default_relationship(active_mode)

    if not os.path.exists(file_path):
        return default_rel
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default_rel
            data = json.loads(content)
            # Ensure relationship_mode is populated
            if "relationship_mode" not in data:
                data["relationship_mode"] = active_mode
            return data
    except Exception:
        return default_rel


def save_relationship(data, user_id: str = "default_user"):
    file_path = get_relationship_file(user_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def reset_companion_data(user_id: str = "default_user", mode: str = "friendship"):
    """Reset chat history, user memory, and relationship for a fresh companion for this user."""
    save_chat_history([], user_id=user_id)
    save_user_memory({}, user_id=user_id)
    initial_relationship = get_default_relationship(mode)
    save_relationship(initial_relationship, user_id=user_id)
    return initial_relationship