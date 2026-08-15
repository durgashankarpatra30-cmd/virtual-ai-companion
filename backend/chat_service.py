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


def is_image_request(message):
    """Check if the user is asking for a photo, picture, or selfie."""
    patterns = [
        r"\b(send|show|give|take|share|post)\b.*?\b(photo|picture|pic|selfie|image|portrait)\b",
        r"\b(photo|picture|pic|selfie|image|portrait)\b.*?\b(of you|please|now)\b",
        r"\bwhat do you look like\b",
        r"\bshow me yourself\b",
        r"\bsend a selfie\b",
        r"\btake a selfie\b",
    ]
    lowered = message.lower()
    for pattern in patterns:
        if re.search(pattern, lowered):
            return True
    return False


def process_message(user_message, is_voice=False, user_audio_url=None):
    # -------------------------------
    # Load fresh data every message
    # -------------------------------
    saved_data = load_companion()

    if not saved_data:
        return {"reply": "No companion found.", "image": None, "audio": None}

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
    )

    user_memory = load_user_memory()
    chat_history = load_chat_history()
    relationship = load_relationship()

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
    )
    save_relationship(relationship)

    # -------------------------------
    # Save important memories
    # -------------------------------
    if should_save_memory(user_message):
        memory = extract_memory(user_message)
        if memory:
            user_memory.update(memory)
            save_user_memory(user_memory)

    # -------------------------------
    # Check if image generation requested
    # -------------------------------
    generated_image = None
    if is_image_request(user_message):
        try:
            print(f"User requested an image. Generating image for {companion.name}...")
            generated_image = generate_companion_image(
                companion=companion,
                custom_scene=f"Taking a cute selfie smiling at the camera for the user",
                is_avatar=False,
            )
        except Exception as e:
            print(f"Could not generate image in chat: {e}")

    # -------------------------------
    # Build AI structured messages
    # -------------------------------
    augmented_message = user_message + (" [Note: You just took and sent a photo/selfie to the user. Mention it naturally in your response!]" if generated_image else "")
    messages = format_chat_messages(
        companion,
        user_memory,
        chat_history,
        augmented_message,
        relationship,
    )

    # -------------------------------
    # Generate AI response
    # -------------------------------
    try:
        response = generate_ai_message(messages, companion=companion, user_message=user_message)
    except Exception as e:
        print(f"AI Engine error: {e}")
        if generated_image:
            response = f"Here's a photo for you! Hope you like it 😊"
        else:
            response = f"I'm right here with you! Tell me what's on your mind, I'm listening."

    # -------------------------------
    # Generate Voice / Audio Speech
    # -------------------------------
    generated_audio = None
    try:
        generated_audio = generate_speech(
            text=response,
            voice_id=companion.voice_id,
            rate=companion.voice_speed,
            pitch=companion.voice_pitch
        )
    except Exception as audio_err:
        print(f"Speech generation error: {audio_err}")

    # -------------------------------
    # Save AI response
    # -------------------------------
    assistant_entry = {
        "role": "assistant",
        "message": response,
    }
    if generated_image:
        assistant_entry["image"] = generated_image["url"]
        assistant_entry["image_data"] = generated_image
    if generated_audio and generated_audio.get("url"):
        assistant_entry["audio"] = generated_audio["url"]
        assistant_entry["audio_data"] = generated_audio

    chat_history.append(assistant_entry)
    save_chat_history(chat_history)

    return {
        "reply": response,
        "image": generated_image["url"] if generated_image else None,
        "image_data": generated_image,
        "audio": generated_audio["url"] if generated_audio else None,
        "audio_data": generated_audio,
    }