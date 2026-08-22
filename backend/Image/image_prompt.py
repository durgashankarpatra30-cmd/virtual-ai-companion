import json
import os
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


# --------------------------------------------------
# CHARACTER / APPEARANCE PROMPT
# --------------------------------------------------

def build_character_prompt(appearance, companion, outfit_override=None):
    name = getattr(companion, "name", None) or appearance.get("name", "Companion")
    gender = getattr(companion, "gender", None) or appearance.get("gender", "Female")
    age = getattr(companion, "age", None) or appearance.get("age", 20)

    is_male = str(gender).lower() in ["male", "man", "boy", "he/him"]
    is_non_binary = str(gender).lower() in ["non-binary", "they/them", "androgynous"]

    # Default styling adapted for gender if not explicitly set
    default_hair = (
        {"color": "dark brown", "style": "short textured modern haircut", "length": "short"}
        if is_male else
        {"color": "black", "style": "long straight", "length": "long"}
    )
    default_clothing = (
        {"top": "stylish dark jacket over fitted tee", "bottom": "dark jeans", "shoes": "clean sneakers"}
        if is_male else
        {"top": "stylish cozy hoodie", "bottom": "blue jeans", "shoes": "white sneakers"}
    )

    hair = appearance.get("hair", default_hair)
    eyes = appearance.get("eyes", {"color": "brown", "shape": "expressive and natural"})
    face = appearance.get("face", {"face_shape": "defined masculine jawline" if is_male else "soft oval"})

    skin_tone = appearance.get("skin_tone", "Fair")
    body_type = appearance.get("body_type", "Athletic" if is_male else "Slim")

    # Handle outfit override dynamically
    if outfit_override and str(outfit_override).strip():
        clean_outfit = str(outfit_override).strip()
        if "saree" in clean_outfit.lower():
            clothing_text = f"Wearing an authentic and elegant {clean_outfit}, beautifully draped with intricate border details and traditional matching jewelry"
        elif "dress" in clean_outfit.lower() or "gown" in clean_outfit.lower():
            clothing_text = f"Wearing a gorgeous and stylish {clean_outfit}"
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

    accessories_list = appearance.get("accessories", [])
    accessories = ", ".join(accessories_list) if accessories_list else "delicate necklace"

    gender_label = "Male" if is_male else ("Person" if is_non_binary else "Female")

    return f"""
Photorealistic portrait photograph of a fictional {age}-year-old {gender_label}.
The character's name is {name}.
Natural human facial proportions, {skin_tone} skin tone, {body_type} body type,
{hair.get('length', '')} {hair.get('color', '')} {hair.get('style', '')} hair,
{eyes.get('color', '')} {eyes.get('shape', '')} eyes, {face.get('face_shape', '')} face.
{clothing_text}.
Accessories: {accessories}.
Maintain consistent character identity, natural human anatomy, realistic facial structure, authentic attire details, and believable physical features.
""".strip()


# --------------------------------------------------
# SCENE PROMPT
# --------------------------------------------------

def build_scene_prompt(state, custom_scene=None):
    if custom_scene and str(custom_scene).strip():
        return f"Scene and activity: The character is {custom_scene.strip()}."

    holding = ", ".join(state.get("holding", [])) if isinstance(state.get("holding"), list) else state.get("holding", "")
    holding_text = f"Holding: {holding}." if holding else ""

    activity = state.get("activity", "relaxing")
    location = state.get("location", "modern cozy room")
    time_of_day = state.get("time_of_day", "afternoon")
    weather = state.get("weather", "Clear")
    pose = state.get("pose", "sitting naturally")

    return f"""
The character is currently {activity} inside/at {location}.
Time of day: {time_of_day}. Weather: {weather}.
Pose: {pose}. {holding_text}
""".strip()


# --------------------------------------------------
# EMOTION PROMPT
# --------------------------------------------------

def build_emotion_prompt(state, custom_mood=None):
    mood = custom_mood or state.get("mood", "Happy")
    emotion = state.get("emotion", "Warm and welcoming")
    expression = state.get("expression", "Gentle natural smile")

    return f"""
Current mood: {mood}. Emotional state: {emotion}.
Facial expression: {expression}.
The emotion should appear subtle, natural, believable, warm, and human. Avoid exaggerated expressions.
""".strip()


# --------------------------------------------------
# CAMERA PROMPT
# --------------------------------------------------

def build_camera_prompt(state, is_selfie=False):
    if is_selfie:
        return "Camera view: Front-facing mobile phone selfie angle, natural arm extension perspective, sharp focus on subject, soft depth of field background."

    camera_view = state.get("camera_view", "Eye-level portrait photograph")
    return f"""
Camera view: {camera_view}.
Natural photographic composition, realistic perspective, natural depth of field, 85mm portrait lens characteristics, soft bokeh background.
""".strip()


# --------------------------------------------------
# QUALITY / PHOTOREALISM PROMPT
# --------------------------------------------------

def build_quality_prompt():
    return """
Photorealistic 8k human photography, realistic skin texture, natural skin pores and subtle imperfections, individual hair strands, lifelike eyes with subtle catchlights, natural facial details, physically plausible lighting, realistic soft shadows, professional photography, cinematic aesthetic, high detail, masterpiece.
Not an illustration, not a cartoon, not anime, not 3D CGI rendering.
""".strip()


# --------------------------------------------------
# FINAL IMAGE PROMPT
# --------------------------------------------------

def build_image_prompt(
    companion,
    state_override=None,
    custom_scene=None,
    outfit_override=None,
    is_selfie=False,
    user_id: str = "default_user",
):
    appearance, base_state = load_image_data(user_id)

    state = dict(base_state)
    if state_override:
        state.update(state_override)

    character_prompt = build_character_prompt(appearance, companion, outfit_override=outfit_override)
    scene_prompt = build_scene_prompt(state, custom_scene=custom_scene)
    emotion_prompt = build_emotion_prompt(state, custom_mood=state.get("mood") if state_override else None)
    camera_prompt = build_camera_prompt(state, is_selfie=is_selfie)
    quality_prompt = build_quality_prompt()

    final_prompt = ", ".join([
        character_prompt.replace("\n", " "),
        scene_prompt.replace("\n", " "),
        emotion_prompt.replace("\n", " "),
        camera_prompt.replace("\n", " "),
        quality_prompt.replace("\n", " ")
    ])

    return final_prompt