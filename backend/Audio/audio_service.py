import os
import hashlib
import asyncio
import edge_tts
from gtts import gTTS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Preset neural voices catalog categorized by gender and style
VOICE_PRESETS = [
    # Female Voices
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (Warm & Expressive)",
        "gender": "Female",
        "style": "Sweet",
        "accent": "US English",
        "description": "Natural, warm, and highly expressive tone.",
    },
    {
        "id": "en-US-AnaNeural",
        "name": "Ana (Sweet & Gentle)",
        "gender": "Female",
        "style": "Sweet",
        "accent": "US English",
        "description": "Youthful, soft, sweet and friendly voice.",
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (Cheerful & Bright)",
        "gender": "Female",
        "style": "Cheerful",
        "accent": "US English",
        "description": "Energetic, cheerful, and lively tone.",
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (Sophisticated British)",
        "gender": "Female",
        "style": "Calm",
        "accent": "British English",
        "description": "Polite, elegant, and soothing British voice.",
    },
    {
        "id": "en-AU-NatashaNeural",
        "name": "Natasha (Friendly Aussie)",
        "gender": "Female",
        "style": "Playful",
        "accent": "Australian English",
        "description": "Upbeat, warm Australian accent.",
    },
    # Male Voices
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (Warm & Casual)",
        "gender": "Male",
        "style": "Sweet",
        "accent": "US English",
        "description": "Natural, friendly, and comforting male voice.",
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (Calm & Deep)",
        "gender": "Male",
        "style": "Calm",
        "accent": "US English",
        "description": "Deep, confident, mature, and reassuring.",
    },
    {
        "id": "en-US-EricNeural",
        "name": "Eric (Upbeat & Playful)",
        "gender": "Male",
        "style": "Cheerful",
        "accent": "US English",
        "description": "Youthful, energetic, and engaging.",
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan (Gentle British)",
        "gender": "Male",
        "style": "Poetic",
        "accent": "British English",
        "description": "Gentle, cultured, and smooth British tone.",
    },
]

def get_default_voice_for_gender(gender: str = "Female") -> str:
    gender_lower = (gender or "Female").lower()
    if "male" in gender_lower and "female" not in gender_lower:
        return "en-US-GuyNeural"
    return "en-US-AriaNeural"

def get_available_voices():
    return VOICE_PRESETS

def clean_text_for_tts(text: str) -> str:
    """Removes all emojis, roleplay actions in asterisks/brackets, and markdown symbols for natural speech."""
    import re
    import unicodedata

    if not text:
        return ""

    # 1. Remove bracket notes like [Note: ...] or [Image: ...]
    clean = re.sub(r"\[.*?\]", "", text)

    # 2. Remove roleplay action asterisks like *smiles warmly* or *whispers softly*
    clean = re.sub(r"\*.*?\*", "", clean)

    # 3. Remove parenthetical action descriptors like (smiling), (giggles softly), (blushing)
    clean = re.sub(r"\((?:smiling|giggling|laughing|whispering|blushing|sighing|softly|tenderly|happily|playfully|gently|gasping|looking|winking|nudging|touching|holding|crying|excitedly)[^)]*\)", "", clean, flags=re.IGNORECASE)

    # 4. Remove all Unicode emoji categories and symbol ranges
    result_chars = []
    for ch in clean:
        cat = unicodedata.category(ch)
        # So: Symbol other (emojis), Sk: Symbol modifier, Cs: Surrogates, Cn: Unassigned
        if cat in ("So", "Sk", "Cs", "Cn"):
            continue
        cp = ord(ch)
        # Miscellaneous symbols, emoticons, supplemental pictographs, variation selectors
        if (0x1F000 <= cp <= 0x1FFFF) or (0x2600 <= cp <= 0x27BF) or (0x2300 <= cp <= 0x23FF) or (0x2B50 <= cp <= 0x2B55) or (0xFE00 <= cp <= 0xFE0F) or (0x200B <= cp <= 0x200D):
            continue
        result_chars.append(ch)
    clean = "".join(result_chars)

    # 5. Clean leftover markdown characters
    clean = re.sub(r"[\*~_`#^<>{}\[\]\\]", "", clean)

    # 6. Normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

async def generate_speech_async(text: str, voice_id: str = "en-US-AriaNeural", rate: str = "+0%", pitch: str = "+0Hz") -> dict:
    """Generates an MP3 audio file for the text using Edge-TTS (or gTTS fallback) and returns the relative URL."""
    if not text or not text.strip():
        return None

    cleaned_text = clean_text_for_tts(text)
    if not cleaned_text:
        cleaned_text = text

    # Generate a unique hash for caching
    content_hash = hashlib.md5(f"{cleaned_text}_{voice_id}_{rate}_{pitch}".encode("utf-8")).hexdigest()
    filename = f"speech_{content_hash}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    relative_url = f"/static/audio/{filename}"

    # Return cached if already exists and has size
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return {
            "url": relative_url,
            "filename": filename,
            "voice": voice_id,
            "cached": True
        }

    try:
        # Edge TTS generation
        communicate = edge_tts.Communicate(
            text=cleaned_text,
            voice=voice_id or "en-US-AriaNeural",
            rate=rate or "+0%",
            pitch=pitch or "+0Hz"
        )
        await communicate.save(filepath)
        
        return {
            "url": relative_url,
            "filename": filename,
            "voice": voice_id,
            "cached": False
        }
    except Exception as e:
        print(f"Edge-TTS synthesis error: {e}. Falling back to gTTS...")
        try:
            tts = gTTS(text=cleaned_text, lang="en")
            tts.save(filepath)
            return {
                "url": relative_url,
                "filename": filename,
                "voice": "gTTS-en",
                "cached": False
            }
        except Exception as gtts_err:
            print(f"gTTS fallback synthesis error: {gtts_err}")
            return None

def generate_speech(text: str, voice_id: str = "en-US-AriaNeural", rate: str = "+0%", pitch: str = "+0Hz") -> dict:
    """Synchronous wrapper for generating speech."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If inside an existing event loop, create a task or new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, generate_speech_async(text, voice_id, rate, pitch)).result()
                return result
        else:
            return loop.run_until_complete(generate_speech_async(text, voice_id, rate, pitch))
    except Exception:
        # Fallback to direct asyncio.run
        try:
            return asyncio.run(generate_speech_async(text, voice_id, rate, pitch))
        except Exception as e:
            print(f"Failed to generate speech in sync wrapper: {e}")
            return None
