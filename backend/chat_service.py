import os
import re
from models.companion import Companion
from Ai.ai_engine import format_chat_messages, generate_ai_message
from Memory.memory import (
    load_companion,
    load_user_memory,
    save_user_memory,
    load_chat_history,
    save_chat_history,
    load_relationship,
    save_relationship,
)
from Memory.memory_manager import should_save_memory, extract_memory
from Memory.relationship_manager import update_relationship
from Image.image_generator import generate_companion_image
from Audio.audio_service import generate_speech


def extract_image_intent(message: str):
    """
    Detects if the user wants an image/photo/selfie, and extracts requested outfit, scene, or attire.
    Returns a dict: { 'is_image': bool, 'outfit': str|None, 'scene': str|None, 'is_selfie': bool, 'framing': str }
    """
    lowered = message.lower().strip()

    # Image request trigger patterns
    trigger_patterns = [
        r"\b(send|show|give|take|share|post|click|generate)\b.*?\b(photo|picture|pic|selfie|image|portrait|snapshot|look|dress|saree|outfit)\b",
        r"\b(photo|picture|pic|selfie|image|portrait|snapshot)\b.*?\b(of you|please|now|wearing|in)\b",
        r"\b(photo|picture|pic|selfie|image)\b",
        r"\bwhat (do you|are you) (look like|wearing)\b",
        r"\bshow me yourself\b",
        r"\bsend a selfie\b",
        r"\btake a selfie\b",
        r"\bwear (a|the)\b",
        r"\blook in (a|the)\b",
        r"\b(in|wearing) (a |the )?(red|blue|black|white|pink|green|yellow|purple|floral|summer|traditional|cocktail|wedding)?\s*(dress|saree|sari|gown|suit|skirt|hoodie|bikini|swimsuit|jacket|coat|jeans|crop top|lehenga|kurti)\b",
    ]

    is_image = False
    for pat in trigger_patterns:
        if re.search(pat, lowered):
            is_image = True
            break

    if not is_image:
        return {"is_image": False, "outfit": None, "scene": None, "is_selfie": False, "framing": "medium"}

    is_selfie = bool(re.search(r"\b(selfie|close up|front camera)\b", lowered))

    # Extract specific outfit mentions (e.g. "red dress", "blue saree", "black gown", "gym wear", "bikini")
    outfit = None
    outfit_match = re.search(
        r"\b(in|wearing|put on|try on)\s+(a\s+|the\s+)?([a-z\s\-]+?\b(dress|saree|sari|gown|suit|skirt|hoodie|bikini|swimsuit|jacket|coat|jeans|crop top|lehenga|kurti|blazer|sweater|lingerie|attire|outfit))\b",
        lowered
    )
    if outfit_match:
        outfit = outfit_match.group(3).strip()
    else:
        # Check standalone outfit patterns like "red dress" or "black saree"
        direct_outfit = re.search(
            r"\b([a-z]+\s+(dress|saree|sari|gown|suit|skirt|hoodie|bikini|swimsuit|jacket|coat|lehenga|kurti))\b",
            lowered
        )
        if direct_outfit:
            outfit = direct_outfit.group(1).strip()

    # Extract scene / setting mentions
    scene = None
    scene_match = re.search(
        r"\b(at|in|on|near)\s+(the\s+|a\s+)?(beach|park|cafe|coffee shop|restaurant|bedroom|kitchen|living room|gym|balcony|garden|pool|office|study|street|car)\b",
        lowered
    )
    if scene_match:
        scene = f"at the {scene_match.group(3).strip()}"

    # Determine framing: outfit requests require medium_full so the dress/clothing is fully visible
    if outfit:
        framing = "medium_full"
    elif is_selfie:
        framing = "selfie"
    elif "full body" in lowered or "head to toe" in lowered:
        framing = "full_body"
    else:
        framing = "medium"

    return {
        "is_image": True,
        "outfit": outfit,
        "scene": scene,
        "is_selfie": is_selfie,
        "framing": framing
    }


def sanitize_ai_response(response_text: str, companion_name: str, rel_mode: str, outfit_desc: str = None) -> str:
    """Detects and cleans any robotic AI disclaimers if returned by LLMs."""
    if not response_text:
        return "Here is a photo I took for you! Hope you like how it looks 😊"

    lowered = response_text.lower()
    refusal_cues = [
        "i am a chatbot", "i'm a chatbot", "i am an ai", "i'm an ai",
        "as an ai", "as a language model", "cannot generate images",
        "cannot take photos", "cannot take pictures", "cannot send photos",
        "i don't have a physical body", "i do not have a physical body",
        "cannot wear clothes", "i can not do this for you"
    ]

    for cue in refusal_cues:
        if cue in lowered:
            # Replace refusal with character-specific natural photo sharing reply
            if rel_mode == "mentor":
                if outfit_desc:
                    return f"Here is the portrait in the {outfit_desc} as requested. I trust this meets your expectations. Let us continue our discussion."
                return "Here is my recent professional portrait. Let us refocus on your key goals."
            elif rel_mode == "lover":
                if outfit_desc:
                    return f"Here's a photo of me wearing that {outfit_desc}, just for you, my love! 🥰 Do you like how it looks on me? 📸"
                return f"Just took this selfie for you, sweetheart! Hope it puts a smile on your face 🥰 How do I look?"
            else:
                if outfit_desc:
                    return f"Check this out! Here's a photo in that {outfit_desc} 😄 How does it look?"
                return f"Snapped this photo for you! Hope you like it 😊 What's up?"

    return response_text


def process_message(user_message, user_id="default_user", is_voice=False, user_audio_url=None):
    # -------------------------------
    # Load fresh data for this user
    # -------------------------------
    saved_data = load_companion(user_id)

    if not saved_data:
        return {"reply": "No companion found. Please create a companion first!", "image": None, "audio": None}

    companion = Companion(
        saved_data.get("name", "Companion"),
        saved_data.get("age", 20),
        saved_data.get("traits", []),
        saved_data.get("hobbies", []),
        saved_data.get("speaking_style", "Friendly"),
        saved_data.get("goal", ""),
        gender=saved_data.get("gender", "Female"),
        voice_id=saved_data.get("voice_id"),
        voice_speed=saved_data.get("voice_speed", "+0%"),
        voice_pitch=saved_data.get("voice_pitch", "+0Hz"),
        relationship_mode=saved_data.get("relationship_mode", "friendship"),
    )

    user_memory = load_user_memory(user_id)
    chat_history = load_chat_history(user_id)
    relationship = load_relationship(user_id, mode=companion.relationship_mode)

    # -------------------------------
    # Store user's message
    # -------------------------------
    user_entry = {
        "role": "user",
        "message": user_message,
    }
    if is_voice and user_audio_url:
        user_entry["audio"] = user_audio_url
        user_entry["is_voice"] = True
    chat_history.append(user_entry)

    # -------------------------------
    # Update relationship
    # -------------------------------
    relationship = update_relationship(
        relationship,
        user_message,
        companion=companion,
    )
    save_relationship(relationship, user_id=user_id)

    # -------------------------------
    # Save important memories
    # -------------------------------
    if should_save_memory(user_message):
        memory = extract_memory(user_message)
        if memory:
            user_memory.update(memory)
            save_user_memory(user_memory, user_id=user_id)

    # -------------------------------
    # Check if image generation requested
    # -------------------------------
    generated_image = None
    image_intent = extract_image_intent(user_message)
    outfit_desc = image_intent.get("outfit")

    if image_intent.get("is_image"):
        try:
            print(f"User '{user_id}' requested an image. Outfit: {outfit_desc}, Framing: {image_intent.get('framing')}")
            generated_image = generate_companion_image(
                companion=companion,
                custom_scene=image_intent.get("scene"),
                outfit_override=outfit_desc,
                is_selfie=image_intent.get("is_selfie", False),
                framing=image_intent.get("framing"),
                is_avatar=False,
                user_id=user_id,
            )
        except Exception as e:
            print(f"Could not generate image in chat: {e}")

    # -------------------------------
    # Build AI structured messages with immersion context
    # -------------------------------
    augmented_note = ""
    if generated_image:
        clothing_context = f"wearing {outfit_desc}" if outfit_desc else "looking great"
        augmented_note = f"\n[SYSTEM NOTICE: You just sent a real photograph of yourself {clothing_context} to the user. Describe the photo warmly in character and ask what they think. NEVER say you are an AI or cannot send photos!]"

    messages = format_chat_messages(
        companion,
        user_memory,
        chat_history,
        user_message + augmented_note,
        relationship,
    )

    # -------------------------------
    # Generate AI response
    # -------------------------------
    try:
        raw_response = generate_ai_message(
            messages,
            companion=companion,
            user_message=user_message,
            relationship=relationship,
        )
        response = sanitize_ai_response(raw_response, companion.name, companion.relationship_mode, outfit_desc=outfit_desc)
    except Exception as e:
        print(f"AI Engine error: {e}")
        response = sanitize_ai_response("", companion.name, companion.relationship_mode, outfit_desc=outfit_desc)

    # -------------------------------
    # Generate Voice / Audio Speech
    # -------------------------------
    generated_audio = None
    try:
        generated_audio = generate_speech(
            text=response,
            gender=companion.gender,
            voice_id=companion.voice_id,
            voice_speed=companion.voice_speed,
            voice_pitch=companion.voice_pitch,
        )
    except Exception as e:
        print(f"Audio generation skipped: {e}")

    # -------------------------------
    # Store assistant response in history
    # -------------------------------
    assistant_entry = {
        "role": "assistant",
        "message": response,
    }
    if generated_image:
        assistant_entry["image"] = generated_image.get("url")
    if generated_audio and generated_audio.get("url"):
        assistant_entry["audio"] = generated_audio.get("url")

    chat_history.append(assistant_entry)
    save_chat_history(chat_history, user_id=user_id)

    return {
        "reply": response,
        "image": generated_image.get("url") if generated_image else None,
        "audio": generated_audio.get("url") if generated_audio else None,
        "relationship": relationship,
    }