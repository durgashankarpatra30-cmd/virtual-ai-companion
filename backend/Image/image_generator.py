import os
import time
import json
import uuid
import urllib.parse
import requests
from models.companion import Companion
from Memory.memory import load_companion
from Image.image_prompt import (
    build_image_prompt,
    load_json,
    save_json,
    get_image_history_file,
    get_state_file,
    get_appearance_file,
)

# Fix SSL issues on Windows Python 3.14
os.environ.pop("SSLKEYLOGFILE", None)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGES_DIR = os.path.join(STATIC_DIR, "images")

# Ensure static directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)


def get_image_history(user_id: str = "default_user"):
    """Retrieve list of previously generated images for the specified user."""
    history_file = get_image_history_file(user_id)
    data = load_json(history_file)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "history" in data:
        return data["history"]
    return []


def save_image_history(history, user_id: str = "default_user"):
    """Save updated image history list for the specified user."""
    history_file = get_image_history_file(user_id)
    save_json(history_file, history)


def get_latest_avatar(user_id: str = "default_user"):
    """Get the current avatar image URL if available for the specified user."""
    history = get_image_history(user_id)
    # First look for an explicitly marked avatar
    for item in reversed(history):
        if item.get("is_avatar"):
            return item
    # Otherwise return the most recent image
    if history:
        return history[-1]
    return None


def set_active_avatar(image_id: str, user_id: str = "default_user"):
    """Set a specific image from history as the active avatar for the user."""
    history = get_image_history(user_id)
    found = False
    for item in history:
        if item.get("id") == image_id:
            item["is_avatar"] = True
            found = True
        else:
            item["is_avatar"] = False

    if found:
        save_image_history(history, user_id)
    return found


def update_companion_state(state_update, user_id: str = "default_user"):
    """Update companion state JSON (activity, location, mood, etc.) for the user."""
    state_file = get_state_file(user_id)
    current_state = load_json(state_file)
    current_state.update(state_update)
    save_json(state_file, current_state)
    return current_state


def generate_companion_image(
    companion=None,
    state_override=None,
    custom_scene=None,
    outfit_override=None,
    is_selfie=False,
    is_avatar=False,
    width=1024,
    height=1024,
    user_id: str = "default_user",
):
    """
    Generates a photorealistic image of the companion using state & appearance,
    saves it locally to static/images/, and records in the user's history.
    """
    # Make sure SSL environment variable is cleared
    os.environ.pop("SSLKEYLOGFILE", None)

    if companion is None:
        saved_data = load_companion(user_id)
        if saved_data:
            companion = Companion(
                saved_data["name"],
                saved_data.get("age", 20),
                saved_data.get("traits", []),
                saved_data.get("hobbies", []),
                saved_data.get("speaking_style", "Sweet"),
                saved_data.get("goal", ""),
                saved_data.get("gender", "Female"),
                relationship_mode=saved_data.get("relationship_mode", "friendship"),
            )
        else:
            companion = Companion(
                "Aaru",
                19,
                ["Kind", "Sweet"],
                ["Dancing", "Reading"],
                "Sweet",
                "Doctor",
                "Female",
                relationship_mode="friendship",
            )

    # Build prompt with outfit and scene overrides
    prompt = build_image_prompt(
        companion,
        state_override=state_override,
        custom_scene=custom_scene,
        outfit_override=outfit_override,
        is_selfie=is_selfie,
        user_id=user_id,
    )

    image_id = str(uuid.uuid4())[:8]
    filename = f"companion_{int(time.time())}_{image_id}.jpg"
    file_path = os.path.join(IMAGES_DIR, filename)
    relative_url = f"/static/images/{filename}"

    # Use Pollinations AI Turbo model for ultra-fast generation
    seed = int(time.time() * 1000) % 1000000
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Use 512 for avatars and fast previews, 768 for studio photos
    img_w = 512 if is_avatar else min(width, 768)
    img_h = 512 if is_avatar else min(height, 768)
    
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={img_w}&height={img_h}&nologo=true&seed={seed}&model=turbo"

    print(f"Generating image for user '{user_id}' with prompt: {prompt[:80]}...")

    headers = {
        "User-Agent": "VirtualCompanionApp/1.0",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=8)
        if response.status_code == 200 and len(response.content) > 1000:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Image successfully saved to {file_path} ({len(response.content)} bytes)")
        else:
            raise Exception(f"Image API returned status: {response.status_code}")

    except Exception as e:
        print(f"Fast image generation attempt failed: {e}")
        # Return None instead of blocking companion creation
        return None

    # Record into history
    scene_label = custom_scene or (state_override.get("activity") if state_override else None) or "Portrait Selfie"
    mood_label = (state_override.get("mood") if state_override else None) or "Happy"

    record = {
        "id": image_id,
        "filename": filename,
        "url": relative_url,
        "full_url": f"http://127.0.0.1:8000{relative_url}",
        "timestamp": int(time.time()),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scene": scene_label,
        "mood": mood_label,
        "prompt": prompt,
        "is_avatar": is_avatar,
    }

    history = get_image_history(user_id)
    if is_avatar:
        for item in history:
            item["is_avatar"] = False
    history.append(record)
    save_image_history(history, user_id)

    return record
