import os
os.environ.pop("SSLKEYLOGFILE", None)
import uuid
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, UploadFile, File
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


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Virtual AI Companion API",
        "version": "1.0.0"
    }


class ChatRequest(BaseModel):
    message: str
    is_voice: Optional[bool] = False
    user_audio_url: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    rate: Optional[str] = "+0%"
    pitch: Optional[str] = "+0Hz"


class VoiceUpdateRequest(BaseModel):
    voice_id: Optional[str] = None
    voice_speed: Optional[str] = None
    voice_pitch: Optional[str] = None


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
    skin_tone: Optional[str] = "Fair"
    hair_color: Optional[str] = None
    hair_style: Optional[str] = None
    eye_color: Optional[str] = None
    clothing_style: Optional[str] = None
    generate_avatar: Optional[bool] = True


@app.get("/")
def home():
    return {"message": "Welcome to virtual AI Companion"}


@app.post("/chat")
def chat(request: ChatRequest):
    result = process_message(
        request.message,
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

    companion = load_companion()
    relationship = load_relationship()
    avatar = get_latest_avatar()

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
def tts_endpoint(request: TTSRequest):
    """Generate audio speech for custom text or voice preview."""
    companion = load_companion()
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
def update_companion_voice(request: VoiceUpdateRequest):
    """Update companion's voice persona settings."""
    companion_data = load_companion()
    if not companion_data:
        raise HTTPException(status_code=404, detail="No companion found")

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
    )
    saved = save_companion(companion)
    return {"success": True, "companion": saved}


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
def get_companion():
    companion = load_companion()
    relationship = load_relationship()
    avatar = get_latest_avatar()

    if not companion:
        return {"exists": False, "error": "No companion found"}

    return {
        "exists": True,
        "name": companion.get("name", "Companion"),
        "gender": companion.get("gender", "Female"),
        "age": companion.get("age", 19),
        "traits": companion.get("traits", []),
        "hobbies": companion.get("hobbies", []),
        "goal": companion.get("goal", ""),
        "speaking_style": companion.get("speaking_style", "Friendly"),
        "voice_id": companion.get("voice_id", get_default_voice_for_gender(companion.get("gender", "Female"))),
        "voice_speed": companion.get("voice_speed", "+0%"),
        "voice_pitch": companion.get("voice_pitch", "+0Hz"),
        "status": "Online",
        "mood": relationship.get("current_mood", "Happy"),
        "friendship_level": relationship.get("friendship_level", 1),
        "total_messages": relationship.get("total_messages", 0),
        "relationship_progress": relationship.get("relationship_progress", 0),
        "relationship_stage": relationship.get("relationship_stage", "New Acquaintance"),
        "avatar": avatar,
        "avatar_url": avatar["url"] if avatar else None,
    }


@app.post("/companion/create")
def create_companion_endpoint(request: CreateCompanionRequest):
    """Creates a new companion, resets memory/chat, updates appearance, and generates initial avatar."""
    default_voice = get_default_voice_for_gender(request.gender)
    companion = Companion(
        name=request.name.strip(),
        age=request.age,
        traits=request.traits if request.traits else ["Kind", "Friendly"],
        hobbies=request.hobbies if request.hobbies else ["Reading", "Music"],
        speaking_style=request.speaking_style or "Friendly",
        goal=request.goal or "Be your best friend",
        gender=request.gender or "Female",
        voice_id=request.voice_id or default_voice,
        voice_speed=request.voice_speed or "+0%",
        voice_pitch=request.voice_pitch or "+0Hz",
    )

    # Save companion to data/companion.json
    saved_companion = save_companion(companion)

    # Reset chat history, memory, and relationship
    initial_relationship = reset_companion_data()

    # Update appearance.json
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
            "bottom": "Comfortable jeans",
            "shoes": "Casual sneakers",
        }

    update_appearance_data(appearance_update)

    # Generate initial avatar if requested
    avatar_record = None
    if request.generate_avatar:
        try:
            print(f"Generating initial avatar portrait for {companion.name} ({companion.gender})...")
            avatar_record = generate_companion_image(
                companion=companion,
                custom_scene=f"Natural portrait smiling warmly at the camera",
                is_avatar=True,
            )
        except Exception as e:
            print(f"Initial avatar generation error: {e}")

    return {
        "success": True,
        "companion": saved_companion,
        "relationship": initial_relationship,
        "avatar": avatar_record or get_latest_avatar(),
    }


@app.get("/history")
def get_chat_history():
    history = load_chat_history()
    return history


@app.post("/generate-image")
def generate_image_endpoint(request: GenerateImageRequest):
    """Generate a new AI image for the companion."""
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
        )
        return {
            "success": True,
            "image": image_record,
        }
    except Exception as e:
        print(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")


@app.get("/image-history")
def get_image_history_endpoint():
    """Get all previously generated images."""
    history = get_image_history()
    return {"history": history}


@app.get("/companion/avatar")
def get_avatar_endpoint():
    """Get the current avatar image."""
    avatar = get_latest_avatar()
    return {"avatar": avatar}


@app.post("/companion/avatar/set")
def set_avatar_endpoint(request: SetAvatarRequest):
    """Set an existing image as active avatar."""
    success = set_active_avatar(request.image_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found in history")
    return {"success": True, "avatar": get_latest_avatar()}


@app.post("/companion/state")
def update_state_endpoint(request: StateUpdateRequest):
    """Update companion state."""
    updates = {k: v for k, v in request.dict().items() if v is not None}
    new_state = update_companion_state(updates)
    return {"success": True, "state": new_state}