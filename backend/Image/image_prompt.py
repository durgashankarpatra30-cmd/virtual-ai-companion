import json
import os
import hashlib
from Memory.memory import get_user_dir

# --------------------------------------------------
# JSON LOADER / SAVER
# --------------------------------------------------

def load_json(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception:
        return {}


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


# --------------------------------------------------
# LOAD / UPDATE IMAGE DATA (PER USER)
# --------------------------------------------------

def get_appearance_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "appearance.json")


def get_state_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "companion_state.json")


def get_image_history_file(user_id: str = "default_user") -> str:
    return os.path.join(get_user_dir(user_id), "image_history.json")


def load_image_data(user_id: str = "default_user"):
    appearance = load_json(get_appearance_file(user_id))
    state = load_json(get_state_file(user_id))
    return appearance, state


def update_appearance_data(new_data, user_id: str = "default_user"):
    file_path = get_appearance_file(user_id)
    current = load_json(file_path)
    current.update(new_data)
    save_json(file_path, current)
    return current


def get_character_seed(companion, user_id: str = "default_user") -> int:
    """Generates a stable deterministic seed for the character to maintain recognizable facial likeness."""
    name = getattr(companion, "name", "Companion")
    gender = getattr(companion, "gender", "Female")
    combined = f"{user_id}_{name}_{gender}_photoreal"
    return int(hashlib.md5(combined.encode("utf-8")).hexdigest(), 16) % 900000 + 100000


# --------------------------------------------------
# HIGH-FIDELITY PHOTOREALISTIC PROMPT BUILDER
# --------------------------------------------------

def build_character_prompt(appearance, companion, outfit_override=None):
    name = getattr(companion, "name", None) or appearance.get("name", "Companion")
    gender = getattr(companion, "gender", None) or appearance.get("gender", "Female")
    age = getattr(companion, "age", None) or appearance.get("age", 20)
    rel_mode = getattr(companion, "relationship_mode", "friendship") or "friendship"

    is_male = str(gender).lower() in ["male", "man", "boy", "he/him"]
    is_non_binary = str(gender).lower() in ["non-binary", "they/them", "androgynous"]

    # Gender styling
    gender_desc = "man" if is_male else ("person" if is_non_binary else "woman")

    default_hair = (
        {"color": "dark brown", "style": "clean textured modern cut", "length": "short"}
        if is_male else
        {"color": "natural black", "style": "straight with soft natural layers", "length": "long"}
    )
    
    if rel_mode == "mentor":
        default_clothing = (
            {"top": "tailored navy blazer over crisp fitted shirt", "bottom": "dark trousers", "shoes": "leather dress shoes"}
            if is_male else
            {"top": "chic tailored blazer over elegant smart top", "bottom": "tailored slacks", "shoes": "minimalist heels"}
        )
    else:
        default_clothing = (
            {"top": "stylish dark casual jacket over fitted tee", "bottom": "fitted dark jeans", "shoes": "clean white sneakers"}
            if is_male else
            {"top": "stylish cozy knit sweater", "bottom": "comfortable blue jeans", "shoes": "clean casual sneakers"}
        )

    hair = appearance.get("hair", default_hair)
    eyes = appearance.get("eyes", {"color": "deep expressive brown", "shape": "natural lifelike"})
    face = appearance.get("face", {"face_shape": "defined masculine jawline" if is_male else "soft natural symmetry"})

    skin_tone = appearance.get("skin_tone", "Fair")
    body_type = appearance.get("body_type", "Athletic" if is_male else "Slim natural")

    # Outfit customization
    if outfit_override and str(outfit_override).strip():
        clean_outfit = str(outfit_override).strip()
        if "saree" in clean_outfit.lower() or "sari" in clean_outfit.lower():
            clothing_text = f"Wearing an authentic elegant {clean_outfit}, beautifully draped with fine fabric weave details and subtle matching jewelry"
        elif "dress" in clean_outfit.lower() or "gown" in clean_outfit.lower():
            clothing_text = f"Wearing a stylish and flattering {clean_outfit}"
        elif "suit" in clean_outfit.lower() or "blazer" in clean_outfit.lower():
            clothing_text = f"Wearing a sharp, well-tailored {clean_outfit}"
        else:
            clothing_text = f"Wearing {clean_outfit}"
    else:
        clothing = appearance.get("clothing", default_clothing)
        top = clothing.get("top", "stylish top")
        bottom = clothing.get("bottom", "casual pants")
        shoes = clothing.get("shoes", "clean sneakers")
        clothing_text = f"Wearing {top}, {bottom}, and {shoes}"

    hair_desc = f"{hair.get('length', '')} {hair.get('color', '')} {hair.get('style', '')} hair with natural shine and realistic individual strands"
    eye_desc = f"{eyes.get('color', 'brown')} eyes with sharp pupil focus, realistic iris depth, and subtle natural light reflections"

    return f"""Raw 8k color portrait photograph of a real, authentic {age}-year-old {gender_desc} named {name}.
Realistic human facial proportions, natural {skin_tone} skin tone with genuine skin texture and subtle natural pores.
{face.get('face_shape', 'natural face')}, {eye_desc}, {hair_desc}.
{clothing_text}.
Maintain recognizable character facial likeness and believable human anatomy."""


def build_scene_prompt(state, custom_scene=None, is_selfie=False):
    if custom_scene and str(custom_scene).strip():
        return f"Scene: {custom_scene.strip()}."

    activity = state.get("activity", "relaxing")
    location = state.get("location", "modern cozy room")
    time_of_day = state.get("time_of_day", "afternoon")
    pose = state.get("pose", "sitting naturally")

    if is_selfie:
        return f"Scene: Taking a front-facing candid selfie with arm extended, smiling warmly at the smartphone camera inside {location}."

    return f"Scene: The subject is currently {activity} at {location} during {time_of_day}, {pose} with natural human posture."


def build_photography_specs(is_selfie=False, is_avatar=False):
    if is_selfie:
        return "Camera angle: Front-facing mobile phone selfie angle, eye-level perspective, sharp focus on face, natural soft background blur, authentic smartphone photography."

    if is_avatar:
        return "Composition: Centered portrait headshot photograph, eye-level shot on Sony A7R V with 85mm f/1.4 GM lens, sharp facial focus, creamy soft background bokeh, natural studio lighting."

    return "Photography specs: Shot on Sony A7R V with 85mm f/1.4 GM portrait lens, natural eye-level framing, authentic depth of field, balanced cinematic lighting, 8k raw photo."


def build_quality_prompt():
    return "Ultra-photorealistic masterpiece, lifelike human skin texture, authentic lighting, highly detailed, real photograph. (Negative prompt: cartoon, illustration, 3D CGI render, anime, drawing, painting, airbrushed plastic skin, deformed fingers, extra limbs, watermark, text, low quality: -1.0)"


def build_image_prompt(
    companion,
    state_override=None,
    custom_scene=None,
    outfit_override=None,
    is_selfie=False,
    is_avatar=False,
    user_id: str = "default_user",
):
    appearance, base_state = load_image_data(user_id)

    state = dict(base_state)
    if state_override:
        state.update(state_override)

    character_part = build_character_prompt(appearance, companion, outfit_override=outfit_override)
    scene_part = build_scene_prompt(state, custom_scene=custom_scene, is_selfie=is_selfie)
    specs_part = build_photography_specs(is_selfie=is_selfie, is_avatar=is_avatar)
    quality_part = build_quality_prompt()

    # Compose clean, rich photographic prompt
    full_prompt = f"{character_part.strip()} {scene_part.strip()} {specs_part.strip()} {quality_part.strip()}"
    return " ".join(full_prompt.split())