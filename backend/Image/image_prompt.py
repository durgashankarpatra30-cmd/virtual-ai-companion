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
    combined = f"{user_id}_{name}_{gender}_photoreal_v3"
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
        {"color": "shiny black", "style": "long straight silky", "length": "long"}
    )
    
    hair = appearance.get("hair", default_hair)
    eyes = appearance.get("eyes", {"color": "deep expressive brown", "shape": "natural lifelike"})
    face = appearance.get("face", {"face_shape": "defined masculine jawline" if is_male else "gorgeous soft natural facial symmetry"})

    skin_tone = appearance.get("skin_tone", "Fair")

    # Outfit customization: cleanly isolated without conflicting clothes
    if outfit_override and str(outfit_override).strip():
        clean_outfit = str(outfit_override).strip()
        if "saree" in clean_outfit.lower() or "sari" in clean_outfit.lower():
            clothing_text = f"Wearing a gorgeous authentic {clean_outfit} with fine silk texture and elegant gold borders"
        elif "dress" in clean_outfit.lower() or "gown" in clean_outfit.lower():
            clothing_text = f"Wearing a stunning, vibrant {clean_outfit} with elegant fabric texture and flattering fit"
        elif "suit" in clean_outfit.lower() or "blazer" in clean_outfit.lower():
            clothing_text = f"Wearing a sharp tailored {clean_outfit} with crisp collar"
        elif "bikini" in clean_outfit.lower() or "swimsuit" in clean_outfit.lower():
            clothing_text = f"Wearing a stylish {clean_outfit}"
        else:
            clothing_text = f"Wearing {clean_outfit}"
    else:
        if rel_mode == "mentor":
            clothing_text = "Wearing a chic tailored blazer over an elegant smart shirt" if not is_male else "Wearing a sharp tailored navy blazer and shirt"
        else:
            clothing_text = "Wearing a stylish cozy top and comfortable casual attire" if not is_male else "Wearing a stylish dark jacket and casual tee"

    hair_desc = f"{hair.get('length', '')} {hair.get('color', '')} {hair.get('style', '')} hair"
    eye_desc = f"{eyes.get('color', 'brown')} eyes with sharp pupil focus and natural light catchlights"

    return f"""stunning raw color photograph of a real, gorgeous {age}-year-old {gender_desc} named {name} with authentic delicate human skin texture, radiant warm smile, beautiful realistic {eye_desc}, and {hair_desc}.
{clothing_text}.
waist-up medium portrait shot, clear detailed face and upper attire prominently in frame, looking directly at camera with natural expression."""


def build_scene_prompt(state, custom_scene=None, is_selfie=False, outfit_override=None):
    if custom_scene and str(custom_scene).strip():
        return f"in a {custom_scene.strip()}."

    location = state.get("location", "modern cozy sunlit room")
    time_of_day = state.get("time_of_day", "daytime")

    if is_selfie:
        return f"taking a warm candid selfie inside {location}."

    return f"in a warm cozy {location} during {time_of_day}."


def build_photography_specs(is_selfie=False, is_avatar=False, framing="medium"):
    if is_avatar:
        return "centered portrait headshot, eye-level framing on 50mm f/1.4 lens, soft creamy background bokeh, studio lighting."

    if is_selfie:
        return "front-facing smartphone camera angle, eye-level, sharp focus on subject, authentic casual photo."

    return "shot on Sony A7R V with 50mm f/1.4 lens, natural depth of field, balanced soft natural lighting, 8k resolution, uncompressed raw color photo, photorealistic masterpiece."


def build_quality_prompt(framing="medium"):
    return "(Negative prompt: blurry face, distorted eyes, ghost face, doll, uncanny, pale ghost, airbrushed plastic skin, cartoon, 3D CGI render, illustration, anime, drawing, painting, deformed fingers, extra limbs, low resolution, bad anatomy: -1.0)"


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

    character_part = build_character_prompt(appearance, companion, outfit_override=outfit_override, framing=framing)
    scene_part = build_scene_prompt(state, custom_scene=custom_scene, is_selfie=is_selfie, outfit_override=outfit_override)
    specs_part = build_photography_specs(is_selfie=is_selfie, is_avatar=is_avatar, framing=framing)
    quality_part = build_quality_prompt(framing=framing)

    full_prompt = f"{character_part.strip()} {scene_part.strip()} {specs_part.strip()} {quality_part.strip()}"
    return " ".join(full_prompt.split())