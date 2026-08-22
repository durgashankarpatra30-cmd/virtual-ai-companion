import os
import time
import json
import uuid
import urllib.parse
import requests
import base64
from models.companion import Companion
from Memory.memory import load_companion
from config import OPENAI_API_KEY, GEMINI_API_KEY, TOGETHER_API_KEY, HF_TOKEN
from Image.image_prompt import (
    build_image_prompt,
    get_character_seed,
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
    for item in reversed(history):
        if item.get("is_avatar"):
            return item
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


# -------------------------------------------------------------
# DALL-E 3 (ChatGPT Image Generation Engine)
# -------------------------------------------------------------
def generate_with_dalle(prompt: str, file_path: str) -> bool:
    if not OPENAI_API_KEY:
        return False
    try:
        print("Attempting generation with OpenAI DALL-E 3 (ChatGPT Engine)...")
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "hd",
            "style": "natural",
        }
        r = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            image_url = data["data"][0]["url"]
            img_res = requests.get(image_url, timeout=20)
            if img_res.status_code == 200 and len(img_res.content) > 5000:
                with open(file_path, "wb") as f:
                    f.write(img_res.content)
                print(f"Successfully generated and saved DALL-E 3 HD image ({len(img_res.content)} bytes)")
                return True
        else:
            print(f"OpenAI DALL-E 3 returned status {r.status_code}: {r.text}")
    except Exception as e:
        print(f"OpenAI DALL-E 3 attempt error: {e}")
    return False


# -------------------------------------------------------------
# Google Imagen & Gemini Image Generation Engine
# -------------------------------------------------------------
def generate_with_gemini_imagen(prompt: str, file_path: str) -> bool:
    if not GEMINI_API_KEY:
        return False
    
    # 1. Try Gemini 2.5/3.1 Flash Image generateContent
    for model_name in ["gemini-2.5-flash-image", "gemini-3.1-flash-image"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": f"Generate a stunning photorealistic 8k color photograph of a real human: {prompt}"}]}],
                "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
            }
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for p in parts:
                        if "inlineData" in p:
                            raw_bytes = base64.b64decode(p["inlineData"]["data"])
                            with open(file_path, "wb") as f:
                                f.write(raw_bytes)
                            print(f"Successfully generated Google {model_name} image ({len(raw_bytes)} bytes)")
                            return True
        except Exception as e:
            print(f"Google {model_name} attempt error: {e}")

    # 2. Try Imagen 3 predict
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "personGeneration": "ALLOW_ADULT"
            }
        }
        r = requests.post(url, headers=headers, json=payload, timeout=25)
        if r.status_code == 200:
            data = r.json()
            predictions = data.get("predictions", [])
            if predictions and "bytesBase64Encoded" in predictions[0]:
                raw_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                with open(file_path, "wb") as f:
                    f.write(raw_bytes)
                print(f"Successfully generated Google Imagen 3 image ({len(raw_bytes)} bytes)")
                return True
    except Exception as e:
        print(f"Google Imagen 3 attempt error: {e}")

    return False


# -------------------------------------------------------------
# Core Unified Image Generator
# -------------------------------------------------------------
def generate_companion_image(
    companion=None,
    state_override=None,
    custom_scene=None,
    outfit_override=None,
    is_selfie=False,
    is_avatar=False,
    framing=None,
    width=None,
    height=None,
    user_id: str = "default_user",
):
    """
    Generates a photorealistic human image using:
    1. OpenAI DALL-E 3 (if OPENAI_API_KEY provided)
    2. Google Imagen 3 (if GEMINI_API_KEY provided)
    3. State-of-the-art Flux Photoreal Engine (Zero-config free tier)
    """
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
                20,
                ["Kind", "Sweet"],
                ["Dancing", "Reading"],
                "Sweet",
                "Doctor",
                "Female",
                relationship_mode="friendship",
            )

    img_w = width or 768
    img_h = height or 768

    # Build photographic prompt
    prompt = build_image_prompt(
        companion,
        state_override=state_override,
        custom_scene=custom_scene,
        outfit_override=outfit_override,
        is_selfie=is_selfie,
        is_avatar=is_avatar,
        framing=framing,
        user_id=user_id,
    )

    image_id = str(uuid.uuid4())[:8]
    filename = f"companion_{int(time.time())}_{image_id}.jpg"
    file_path = os.path.join(IMAGES_DIR, filename)
    relative_url = f"/static/images/{filename}"

    # Try Tier 1: OpenAI DALL-E 3 / ChatGPT
    if generate_with_dalle(prompt, file_path):
        pass
    # Try Tier 2: Google Imagen 3
    elif generate_with_gemini_imagen(prompt, file_path):
        pass
    # Tier 3: Zero-Config Free Flux Photoreal Engine
    else:
        char_base_seed = get_character_seed(companion, user_id=user_id)
        scene_seed = (char_base_seed + (int(time.time()) % 150)) if not is_avatar else char_base_seed
        encoded_prompt = urllib.parse.quote(prompt)

        models_to_try = [
            "flux",
            "flux-realism",
            "turbo"
        ]

        headers = {
            "User-Agent": "VirtualCompanionAI/4.0",
        }

        image_saved = False
        for model_name in models_to_try:
            try:
                api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={img_w}&height={img_h}&nologo=true&seed={scene_seed}&model={model_name}"
                print(f"Generating photorealistic image ({model_name}, {img_w}x{img_h}) for {companion.name}...")
                
                response = requests.get(api_url, headers=headers, timeout=16)
                if response.status_code == 200 and len(response.content) > 3000:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"Image ({model_name}) saved to {file_path} ({len(response.content)} bytes)")
                    image_saved = True
                    break
            except Exception as err:
                print(f"Model {model_name} attempt failed: {err}")

        if not image_saved:
            print("Image generation failed across all fallback engines.")
            return None

    # Record into history
    scene_label = custom_scene or (state_override.get("activity") if state_override else None) or (f"Outfit: {outfit_override}" if outfit_override else ("Selfie" if is_selfie else "Portrait"))
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
        "outfit": outfit_override,
        "is_avatar": is_avatar,
    }

    history = get_image_history(user_id)
    if is_avatar:
        for item in history:
            item["is_avatar"] = False
    history.append(record)
    save_image_history(history, user_id)

    return record
