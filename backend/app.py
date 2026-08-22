import os
os.environ.pop("SSLKEYLOGFILE", None)
import uuid
import re
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chat_service import process_message
from models.companion import Companion
from Memory.memory import (
    load_companion,
    save_companion,
    load_relationship,
    load_chat_history,
    reset_companion_data,
    save_relationship,
)
from Image.image_generator import (
    generate_companion_image,
    get_image_history,
    get_latest_avatar,
    set_active_avatar,
    update_companion_state,
    STATIC_DIR,
)
from Image.image_prompt import update_appearance_data
from Audio.audio_service import (
    get_available_voices,
    generate_speech,
    get_default_voice_for_gender,
    AUDIO_DIR,
)
from Date.date_engine import (
    DATE_VENUES,
    start_date_session,
    execute_date_action,
    finish_date_session,
    get_all_date_memories,
    load_relationship_metrics,
)

app = FastAPI(title="Virtual AI Companion API")

# Mount static folder for serving generated companion images and audio
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
USER_AUDIO_DIR = os.path.join(AUDIO_DIR, "user_recordings")
os.makedirs(USER_AUDIO_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Enable CORS for all frontend domains (Vercel, Localhost, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_user_id(header_user_id: Optional[str] = None, fallback_id: Optional[str] = None) -> str:
    """Safely extracts and sanitizes user ID from request headers or body."""
    raw_id = header_user_id or fallback_id or "default_user"
    clean = re.sub(r"[^a-zA-Z0-9_-]", "", str(raw_id).strip())
    return clean if clean else "default_user"


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Virtual AI Companion API",
        "version": "2.0.0",
        "multi_user_isolation": True,
        "relationship_modes": ["friendship", "mentor", "lover"]
    }


class ChatRequest(BaseModel):
    message: str
    is_voice: Optional[bool] = False
    user_audio_url: Optional[str] = None
    user_id: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    rate: Optional[str] = "+0%"
    pitch: Optional[str] = "+0Hz"


class VoiceUpdateRequest(BaseModel):
    voice_id: Optional[str] = None
    voice_speed: Optional[str] = None
    voice_pitch: Optional[str] = None
    relationship_mode: Optional[str] = None


class GenerateImageRequest(BaseModel):
    scene: Optional[str] = None
    mood: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    is_avatar: Optional[bool] = False
    custom_prompt: Optional[str] = None


class SetAvatarRequest(BaseModel):
    image_id: str


class StateUpdateRequest(BaseModel):
    activity: Optional[str] = None
    mood: Optional[str] = None
    emotion: Optional[str] = None
    location: Optional[str] = None
    expression: Optional[str] = None
    outfit: Optional[str] = None
    pose: Optional[str] = None


class RelationshipModeUpdateRequest(BaseModel):
    mode: str


class StartDateRequest(BaseModel):
    venue_id: str


class DateActionRequest(BaseModel):
    session_id: str
    choice_id: Optional[str] = None
    message: Optional[str] = None


class FinishDateRequest(BaseModel):
    session_id: str
    rating: Optional[str] = "Amazing"
    feedback: Optional[str] = None


class CreateCompanionRequest(BaseModel):
    name: str
    gender: str = "Female"
    age: int = 20
    traits: List[str] = []
    hobbies: List[str] = []
    speaking_style: str = "Sweet"
    goal: str = ""
    voice_id: Optional[str] = None
    voice_speed: Optional[str] = "+0%"
    voice_pitch: Optional[str] = "+0Hz"
    relationship_mode: Optional[str] = "friendship"
    skin_tone: Optional[str] = "Fair"
    hair_color: Optional[str] = None
    hair_style: Optional[str] = None
    eye_color: Optional[str] = None
    clothing_style: Optional[str] = None
    generate_avatar: Optional[bool] = True


@app.post("/chat")
def chat(request: ChatRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    user_id = extract_user_id(x_user_id, request.user_id)
    result = process_message(
        request.message,
        user_id=user_id,
        is_voice=request.is_voice or False,
        user_audio_url=request.user_audio_url
    )

    if isinstance(result, dict):
        reply = result.get("reply", "")
        image = result.get("image", None)
        image_data = result.get("image_data", None)
        audio = result.get("audio", None)
        audio_data = result.get("audio_data", None)
    else:
        reply = str(result)
        image = None
        image_data = None
        audio = None
        audio_data = None

    companion = load_companion(user_id)
    relationship = load_relationship(user_id, mode=companion.get("relationship_mode") if companion else "friendship")
    avatar = get_latest_avatar(user_id)

    return {
        "reply": reply,
        "image": image,
        "image_data": image_data,
        "audio": audio,
        "audio_data": audio_data,
        "companion": companion,
        "relationship": relationship,
        "avatar": avatar,
    }


@app.get("/voices")
def get_voices():
    """List available neural voices with metadata."""
    return {"voices": get_available_voices()}


@app.post("/tts")
def tts_endpoint(request: TTSRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Generate audio speech for custom text or voice preview."""
    user_id = extract_user_id(x_user_id)
    companion = load_companion(user_id)
    default_voice = companion.get("voice_id") if companion else "en-US-AriaNeural"
    voice = request.voice_id or default_voice or "en-US-AriaNeural"
    
    audio_record = generate_speech(
        text=request.text,
        voice_id=voice,
        rate=request.rate or "+0%",
        pitch=request.pitch or "+0Hz"
    )
    if not audio_record:
        raise HTTPException(status_code=500, detail="TTS synthesis failed")
    
    return {"success": True, "audio": audio_record}


@app.post("/companion/voice")
def update_companion_voice(request: VoiceUpdateRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Update companion's voice persona and relationship mode settings."""
    user_id = extract_user_id(x_user_id)
    companion_data = load_companion(user_id)
    if not companion_data:
        raise HTTPException(status_code=404, detail="No companion found for this profile")

    rel_mode = request.relationship_mode or companion_data.get("relationship_mode", "friendship")

    companion = Companion(
        name=companion_data.get("name", "Companion"),
        age=companion_data.get("age", 20),
        traits=companion_data.get("traits", []),
        hobbies=companion_data.get("hobbies", []),
        speaking_style=companion_data.get("speaking_style", "Friendly"),
        goal=companion_data.get("goal", ""),
        gender=companion_data.get("gender", "Female"),
        voice_id=request.voice_id or companion_data.get("voice_id", "en-US-AriaNeural"),
        voice_speed=request.voice_speed or companion_data.get("voice_speed", "+0%"),
        voice_pitch=request.voice_pitch or companion_data.get("voice_pitch", "+0Hz"),
        relationship_mode=rel_mode,
    )
    saved = save_companion(companion, user_id=user_id)

    # Sync relationship mode if updated
    if request.relationship_mode:
        rel = load_relationship(user_id, mode=rel_mode)
        rel["relationship_mode"] = rel_mode
        save_relationship(rel, user_id=user_id)

    return {"success": True, "companion": saved}


@app.post("/companion/relationship-mode")
def update_relationship_mode(request: RelationshipModeUpdateRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Update companion's relationship mode (friendship, mentor, lover)."""
    user_id = extract_user_id(x_user_id)
    companion_data = load_companion(user_id)
    if not companion_data:
        raise HTTPException(status_code=404, detail="No companion found for this profile")

    mode = request.mode.lower().strip()
    if mode not in ["friendship", "mentor", "lover"]:
        mode = "friendship"

    companion_data["relationship_mode"] = mode
    companion = Companion(
        name=companion_data.get("name", "Companion"),
        age=companion_data.get("age", 20),
        traits=companion_data.get("traits", []),
        hobbies=companion_data.get("hobbies", []),
        speaking_style=companion_data.get("speaking_style", "Friendly"),
        goal=companion_data.get("goal", ""),
        gender=companion_data.get("gender", "Female"),
        voice_id=companion_data.get("voice_id"),
        voice_speed=companion_data.get("voice_speed", "+0%"),
        voice_pitch=companion_data.get("voice_pitch", "+0Hz"),
        relationship_mode=mode,
    )
    saved = save_companion(companion, user_id=user_id)

    # Update relationship stage label for the new mode
    rel = load_relationship(user_id, mode=mode)
    rel["relationship_mode"] = mode
    save_relationship(rel, user_id=user_id)

    return {"success": True, "companion": saved, "relationship": rel}


@app.post("/transcribe-audio")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Receives recorded user audio, saves it, and returns the audio URL."""
    try:
        ext = os.path.splitext(file.filename)[1] or ".webm"
        unique_name = f"user_{uuid.uuid4().hex[:10]}{ext}"
        save_path = os.path.join(USER_AUDIO_DIR, unique_name)
        
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
            
        relative_url = f"/static/audio/user_recordings/{unique_name}"
        return {
            "success": True,
            "url": relative_url,
            "filename": unique_name
        }
    except Exception as e:
        print(f"Error handling audio upload: {e}")
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")


@app.get("/companion")
def get_companion(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    user_id = extract_user_id(x_user_id)
    companion = load_companion(user_id)
    avatar = get_latest_avatar(user_id)

    if not companion:
        return {"exists": False, "error": "No companion found for this profile", "user_id": user_id}

    rel_mode = companion.get("relationship_mode", "friendship") or "friendship"
    relationship = load_relationship(user_id, mode=rel_mode)

    return {
        "exists": True,
        "user_id": user_id,
        "name": companion.get("name", "Companion"),
        "gender": companion.get("gender", "Female"),
        "age": companion.get("age", 19),
        "traits": companion.get("traits", []),
        "hobbies": companion.get("hobbies", []),
        "goal": companion.get("goal", ""),
        "speaking_style": companion.get("speaking_style", "Friendly"),
        "relationship_mode": rel_mode,
        "voice_id": companion.get("voice_id", get_default_voice_for_gender(companion.get("gender", "Female"))),
        "voice_speed": companion.get("voice_speed", "+0%"),
        "voice_pitch": companion.get("voice_pitch", "+0Hz"),
        "status": "Online",
        "mood": relationship.get("current_mood", "Happy"),
        "friendship_level": relationship.get("friendship_level", 1),
        "total_messages": relationship.get("total_messages", 0),
        "relationship_progress": relationship.get("relationship_progress", 0),
        "relationship_stage": relationship.get("relationship_stage", "New Acquaintance"),
        "relationship": relationship,
        "avatar": avatar,
        "avatar_url": avatar["url"] if avatar else None,
    }


@app.post("/companion/create")
def create_companion_endpoint(request: CreateCompanionRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Creates a new companion for the specific user/device, resets their memory/chat, updates appearance, and generates initial avatar."""
    user_id = extract_user_id(x_user_id)
    default_voice = get_default_voice_for_gender(request.gender)
    rel_mode = (request.relationship_mode or "friendship").lower().strip()
    if rel_mode not in ["friendship", "mentor", "lover"]:
        rel_mode = "friendship"

    companion = Companion(
        name=request.name.strip(),
        age=request.age,
        traits=request.traits if request.traits else ["Kind", "Friendly"],
        hobbies=request.hobbies if request.hobbies else ["Reading", "Music"],
        speaking_style=request.speaking_style or "Friendly",
        goal=request.goal or ("Provide inspiring guidance" if rel_mode == "mentor" else "Be your best friend"),
        gender=request.gender or "Female",
        voice_id=request.voice_id or default_voice,
        voice_speed=request.voice_speed or "+0%",
        voice_pitch=request.voice_pitch or "+0Hz",
        relationship_mode=rel_mode,
    )

    # Save companion to data/users/<user_id>/companion.json
    saved_companion = save_companion(companion, user_id=user_id)

    # Reset chat history, memory, and relationship for this user
    initial_relationship = reset_companion_data(user_id=user_id, mode=rel_mode)

    # Update appearance.json for this user
    is_male = str(request.gender).lower() in ["male", "man", "boy"]
    appearance_update = {
        "name": request.name,
        "gender": request.gender,
        "age": request.age,
        "skin_tone": request.skin_tone or "Fair",
    }

    hair_dict = {}
    if request.hair_color:
        hair_dict["color"] = request.hair_color
    if request.hair_style:
        hair_dict["style"] = request.hair_style
        hair_dict["length"] = "Short" if is_male else "Long"
    if hair_dict:
        appearance_update["hair"] = hair_dict

    if request.eye_color:
        appearance_update["eyes"] = {"color": request.eye_color, "shape": "Expressive"}

    if request.clothing_style:
        appearance_update["clothing"] = {
            "top": request.clothing_style,
            "bottom": "Comfortable pants",
            "shoes": "Clean sneakers",
        }

    update_appearance_data(appearance_update, user_id=user_id)

    # Generate initial avatar if requested
    avatar_record = None
    if request.generate_avatar:
        try:
            print(f"Generating initial avatar portrait for {companion.name} ({companion.gender}) [User: {user_id}]...")
            scene_text = "Professional portrait in formal attire" if rel_mode == "mentor" else "Natural portrait smiling warmly at the camera"
            avatar_record = generate_companion_image(
                companion=companion,
                custom_scene=scene_text,
                is_avatar=True,
                user_id=user_id,
            )
        except Exception as e:
            print(f"Initial avatar generation error: {e}")

    return {
        "success": True,
        "user_id": user_id,
        "companion": saved_companion,
        "relationship": initial_relationship,
        "avatar": avatar_record or get_latest_avatar(user_id),
    }


@app.get("/history")
def get_chat_history(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    user_id = extract_user_id(x_user_id)
    history = load_chat_history(user_id)
    return history


@app.post("/generate-image")
def generate_image_endpoint(request: GenerateImageRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Generate a new AI image for the companion."""
    user_id = extract_user_id(x_user_id)
    state_override = {}
    if request.activity:
        state_override["activity"] = request.activity
    if request.mood:
        state_override["mood"] = request.mood
    if request.location:
        state_override["location"] = request.location

    try:
        image_record = generate_companion_image(
            state_override=state_override if state_override else None,
            custom_scene=request.scene or request.custom_prompt,
            is_avatar=request.is_avatar or False,
            user_id=user_id,
        )
        return {
            "success": True,
            "image": image_record,
        }
    except Exception as e:
        print(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")


@app.get("/image-history")
def get_image_history_endpoint(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Get all previously generated images for the user."""
    user_id = extract_user_id(x_user_id)
    history = get_image_history(user_id)
    return {"history": history}


@app.get("/companion/avatar")
def get_avatar_endpoint(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Get the current avatar image for the user."""
    user_id = extract_user_id(x_user_id)
    avatar = get_latest_avatar(user_id)
    return {"avatar": avatar}


@app.post("/companion/avatar/set")
def set_avatar_endpoint(request: SetAvatarRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Set an existing image as active avatar for the user."""
    user_id = extract_user_id(x_user_id)
    success = set_active_avatar(request.image_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found in history")
    return {"success": True, "avatar": get_latest_avatar(user_id)}


@app.post("/companion/state")
def update_state_endpoint(request: StateUpdateRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Update companion state."""
    user_id = extract_user_id(x_user_id)
    updates = {k: v for k, v in request.dict().items() if v is not None}
    new_state = update_companion_state(updates, user_id=user_id)
    return {"success": True, "state": new_state}


# -------------------------------------------------------------
# Virtual Date & Interactive Experience Endpoints
# -------------------------------------------------------------
@app.get("/date/destinations")
def get_date_destinations(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Returns available date venues, user metrics, and proactive companion invite."""
    user_id = extract_user_id(x_user_id)
    metrics = load_relationship_metrics(user_id)
    companion = load_companion(user_id)
    name = companion.get("name", "Companion") if companion else "Companion"
    rel_mode = companion.get("relationship_mode", "friendship") if companion else "friendship"

    # Pick a recommended venue
    rec_venue = DATE_VENUES[0]
    if rel_mode == "lover":
        rec_venue = next((v for v in DATE_VENUES if v["id"] == "sunset_city_walk"), DATE_VENUES[1])
        invite_msg = f"I've been dreaming about going on a {rec_venue['name']} with you today, my love! Want to go? ✨"
    elif rel_mode == "mentor":
        rec_venue = next((v for v in DATE_VENUES if v["id"] == "coffee_cafe"), DATE_VENUES[0])
        invite_msg = f"A session at {rec_venue['name']} would offer great clarity and fresh perspective today."
    else:
        rec_venue = next((v for v in DATE_VENUES if v["id"] == "gaming_lounge"), DATE_VENUES[4])
        invite_msg = f"Hey! How about we hang out at the {rec_venue['name']} today? It's going to be so fun! 🎮"

    return {
        "destinations": DATE_VENUES,
        "metrics": metrics,
        "recommended_venue": rec_venue,
        "proactive_invite": invite_msg,
        "relationship_mode": rel_mode
    }


@app.post("/date/start")
def start_date_endpoint(request: StartDateRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Initializes a new interactive date session."""
    user_id = extract_user_id(x_user_id)
    session = start_date_session(request.venue_id, user_id=user_id)
    return session


@app.post("/date/action")
def date_action_endpoint(request: DateActionRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Processes a user's date choice or text response."""
    user_id = extract_user_id(x_user_id)
    result = execute_date_action(
        session_id=request.session_id,
        choice_id=request.choice_id,
        custom_message=request.message,
        user_id=user_id
    )
    return result


@app.post("/date/finish")
def finish_date_endpoint(request: FinishDateRequest, x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Concludes the date session and generates a collectible Date Memory Card."""
    user_id = extract_user_id(x_user_id)
    result = finish_date_session(
        session_id=request.session_id,
        rating=request.rating or "Amazing",
        user_feedback=request.feedback,
        user_id=user_id
    )
    return result


@app.get("/date/history")
def get_date_history_endpoint(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    """Retrieves all past Date Memory Cards for the user."""
    user_id = extract_user_id(x_user_id)
    memories = get_all_date_memories(user_id)
    metrics = load_relationship_metrics(user_id)
    return {
        "memories": memories,
        "metrics": metrics,
        "total_dates": len(memories)
    }