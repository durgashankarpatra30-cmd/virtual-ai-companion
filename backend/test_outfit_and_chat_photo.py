import sys
import os

# Fix SSL on Python 3.14 Windows
os.environ.pop("SSLKEYLOGFILE", None)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app import app
from chat_service import extract_image_intent, sanitize_ai_response

client = TestClient(app)

def test_outfit_extraction_and_photo_chat():
    print("\n--- Testing Outfit Extraction & Chat Photo Response ---", flush=True)

    # 1. Test Intent & Outfit Extraction
    msg1 = "send photo in red dress"
    intent1 = extract_image_intent(msg1)
    print(f"Message: '{msg1}' -> Intent: {intent1}", flush=True)
    assert intent1["is_image"] is True
    assert "red dress" in intent1["outfit"]
    assert intent1["framing"] == "medium_full"

    msg2 = "can you send a pic in black saree at the beach"
    intent2 = extract_image_intent(msg2)
    print(f"Message: '{msg2}' -> Intent: {intent2}", flush=True)
    assert intent2["is_image"] is True
    assert "saree" in intent2["outfit"]
    assert "beach" in intent2["scene"]
    assert intent2["framing"] == "medium_full"

    msg3 = "take a selfie please"
    intent3 = extract_image_intent(msg3)
    print(f"Message: '{msg3}' -> Intent: {intent3}", flush=True)
    assert intent3["is_image"] is True
    assert intent3["is_selfie"] is True

    # 2. Test AI Refusal Sanitizer
    refusal_raw = "I am a chatbot and I cannot generate images or take photos for you now."
    cleaned = sanitize_ai_response(refusal_raw, "Aaru", "lover", outfit_desc="red dress")
    print(f"\nRaw Refusal: '{refusal_raw}'\nSanitized Response: '{cleaned}'", flush=True)
    assert "chatbot" not in cleaned.lower()
    assert "red dress" in cleaned.lower()

    # 3. End-to-End Chat Test with Outfit Request
    user_test_id = "test_user_red_dress"
    
    # Create a companion first
    create_res = client.post(
        "/companion/create",
        headers={"X-User-Id": user_test_id},
        json={
            "name": "Maya",
            "gender": "Female",
            "age": 21,
            "relationship_mode": "lover",
            "traits": ["Sweet", "Loving"],
            "hobbies": ["Fashion", "Art"],
            "speaking_style": "Sweet",
            "goal": "Be your loving partner",
            "generate_avatar": False
        }
    )
    assert create_res.status_code == 200

    print("\nSending chat message: 'send photo in red dress'...", flush=True)
    chat_res = client.post(
        "/chat",
        headers={"X-User-Id": user_test_id},
        json={"message": "send photo in red dress"}
    ).json()

    print(f"Companion Reply Text: {chat_res['reply']}", flush=True)
    print(f"Companion Image URL: {chat_res.get('image')}", flush=True)

    assert chat_res.get("image") is not None, "Expected an image to be generated and attached!"
    assert "chatbot" not in chat_res["reply"].lower()
    assert "cannot" not in chat_res["reply"].lower()

    print("\n==========================================", flush=True)
    print("ALL OUTFIT & PHOTO CHAT TESTS PASSED!", flush=True)
    print("==========================================\n", flush=True)

if __name__ == "__main__":
    test_outfit_extraction_and_photo_chat()
