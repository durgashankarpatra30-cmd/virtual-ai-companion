import json
import os
import hashlib
import re
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
    combined = f"{user_id}_{name}_{gender}_photoreal_v2"
    return int(hashlib.md5(combined.encode("utf-8")).hexdigest(), 16) % 900000 + 100000


# --------------------------------------------------
# HIGH-FIDELITY PHOTOREALISTIC PROMPT BUILDER
# --------------------------------------------------

def build_character_prompt(appearance, companion, outfit_override=None, framing="medium"):
    name = getattr(companion, "name", None) or appearance.get("name", "Companion")
    gender = getattr(companion, "gender", None) or appearance.get("gender", "Female")
    age = getattr(companion, "age", None) or appearance.get("age", 20)
    rel_mode = getattr(companion, "relationship_mode", "friendship") or "friendship"

    is_male = str(gender).lower() in ["male", "man", "boy", "he/him"]
    is_non_binary = str(gender).lower() in ["non-binary", "they/them", "androgynous"]

    gender_desc = "man" if is_male else ("person" if is_non_binary else "woman")

    default_hair = (
        {"color": "dark brown", "style": "clean textured modern cut", "length": "short"}
        if is_male else
        {"color": "natural black", "style": "straight with soft natural layers", "length": "long"}
    )
    
    hair = appearance.get("hair", default_hair)
    eyes = appearance.get("eyes", {"color": "deep expressive brown", "shape": "natural lifelike"})
    face = appearance.get("face", {"face_shape": "defined masculine jawline" if is_male else "soft natural symmetry"})

    skin_tone = appearance.get("skin_tone", "Fair")
    body_type = appearance.get("body_type", "Athletic" if is_male else "Slim natural")

    # Outfit customization & Full-body framing
    if outfit_override and str(outfit_override).strip():
        clean_outfit = str(outfit_override).strip()
        if "saree" in clean_outfit.lower() or "sari" in clean_outfit.lower():
            clothing_text = f"Wearing a gorgeous, authentic {clean_outfit}, beautifully draped with intricate fabric texture, gold borders, and matching traditional accessories. Full attire clearly visible"
        elif "dress" in clean_outfit.lower() or "gown" in clean_outfit.lower():
            clothing_text = f"Wearing an eye-catching, elegant {clean_outfit} tailored with realistic fabric texture, natural folds, and graceful drape. The full dress is prominently visible from shoulders to below knees"
        elif "suit" in clean_outfit.lower() or "blazer" in clean_outfit.lower():
            clothing_text = f"Wearing a sharp, well-tailored {clean_outfit} with crisp collar and matching trousers. Full formal outfit prominently visible"
        elif "bikini" in clean_outfit.lower() or "swimsuit" in clean_outfit.lower() or "swimwear" in clean_outfit.lower():
            clothing_text = f"Wearing a stylish {clean_outfit}, beachwear style"
        else:
            clothing_text = f"Wearing {clean_outfit}, with the complete outfit and clothing clearly displayed in the frame"
    else:
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
        clothing = appearance.get("clothing", default_clothing)
        top = clothing.get("top", "stylish top")
        bottom = clothing.get("bottom", "casual pants")
        shoes = clothing.get("shoes", "clean sneakers")
        clothing_text = f"Wearing {top}, {bottom}, and {shoes}"

    hair_desc = f"{hair.get('length', '')} {hair.get('color', '')} {hair.get('style', '')} hair with natural shine and individual strands"
    eye_desc = f"{eyes.get('color', 'brown')} eyes with sharp focus and subtle natural light reflections"

    if framing in ["full_body", "medium_full"]:
        frame_intro = f"Raw 8k color fashion photograph of a real, authentic {age}-year-old {gender_desc} named {name}. Medium full-body shot showing the full body and attire from head to knees."
    elif framing == "selfie":
        frame_intro = f"Raw 8k color candid selfie photograph of a real, authentic {age}-year-old {gender_desc} named {name} holding phone at arm's length."
    else:
        frame_intro = f"Raw 8k color portrait photograph of a real, authentic {age}-year-old {gender_desc} named {name}."

    return f"""{frame_intro}
Realistic human facial proportions, natural {skin_tone} skin tone with genuine skin texture and subtle natural pores.
{face.get('face_shape', 'natural face')}, {eye_desc}, {hair_desc}.
{clothing_text}.
Maintain recognizable character facial likeness and authentic human anatomy."""


def build_scene_prompt(state, custom_scene=None, is_selfie=False, outfit_override=None):
    if custom_scene and str(custom_scene).strip():
        return f"Scene & Setting: {custom_scene.strip()}."

    location = state.get("location", "modern cozy room")
    time_of_day = state.get("time_of_day", "afternoon")

    if is_selfie:
        return f"Scene: Taking a smiling candid selfie, posing naturally inside {location}."

    if outfit_override:
        return f"Scene: Posing gracefully in a modern setting, standing naturally and showcasing the complete outfit during {time_of_day}."

    activity = state.get("activity", "relaxing")
    pose = state.get("pose", "standing naturally")
    return f"Scene: The subject is {activity} at {location}, {pose} with natural relaxed posture."


def build_photography_specs(is_selfie=False, is_avatar=False, framing="medium"):
    if is_avatar:
        return "Composition: Centered portrait headshot photograph, eye-level shot on 85mm f/1.4 lens, creamy soft background bokeh, natural studio lighting."

    if is_selfie:
        return "Camera angle: Front-facing mobile smartphone camera angle, eye-level perspective, sharp focus on subject, authentic casual photo."

    if framing in ["full_body", "medium_full"]:
        return "Framing: Medium full-body shot standing and posing, wide angle 50mm lens capturing the complete outfit from head to below knees, balanced cinematic lighting, full attire clearly in frame, soft depth of field."

    return "Photography specs: Shot on Sony A7R V with 50mm lens, eye-level framing, authentic depth of field, balanced natural lighting, 8k raw photo."


def build_quality_prompt(framing="medium"):
    neg = "cropped headshot, close-up face only, cut off dress, cartoon, illustration, 3D CGI render, anime, drawing, painting, airbrushed plastic skin, deformed fingers, extra limbs, watermark, text, low quality: -1.0"
    if framing in ["full_body", "medium_full"]:
        return f"Ultra-photorealistic masterpiece, lifelike human skin texture, authentic fabric texture and drape, highly detailed, real photograph. (Negative prompt: {neg})"
    return f"Ultra-photorealistic masterpiece, lifelike human skin texture, authentic lighting, highly detailed, real photograph. (Negative prompt: cartoon, illustration, 3D CGI render, anime, drawing, painting, airbrushed plastic skin, deformed fingers, extra limbs, watermark, text, low quality: -1.0)"


def build_image_prompt(
    companion,
    state_override=None,
    custom_scene=None,
    outfit_override=None,
    is_selfie=False,
    is_avatar=False,
    framing=None,
    user_id: str = "default_user",
):
    appearance, base_state = load_image_data(user_id)

    state = dict(base_state)
    if state_override:
        state.update(state_override)

    # Determine framing automatically if outfit or full body is requested
    if framing is None:
        if is_avatar:
            framing = "headshot"
        elif is_selfie:
            framing = "selfie"
        elif outfit_override and any(w in str(outfit_override).lower() for w in ["dress", "saree", "sari", "gown", "suit", "skirt", "pants", "bikini", "outfit", "coat", "jacket", "jeans"]):
            framing = "medium_full"
        else:
            framing = "medium"

    character_part = build_character_prompt(appearance, companion, outfit_override=outfit_override, framing=framing)
    scene_part = build_scene_prompt(state, custom_scene=custom_scene, is_selfie=is_selfie, outfit_override=outfit_override)
    specs_part = build_photography_specs(is_selfie=is_selfie, is_avatar=is_avatar, framing=framing)
    quality_part = build_quality_prompt(framing=framing)

    full_prompt = f"{character_part.strip()} {scene_part.strip()} {specs_part.strip()} {quality_part.strip()}"
    return " ".join(full_prompt.split())