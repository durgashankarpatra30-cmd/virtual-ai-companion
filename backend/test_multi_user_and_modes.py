import sys
import os

# Fix SSL on Python 3.14 Windows
os.environ.pop("SSLKEYLOGFILE", None)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app
from Memory.memory import load_companion, load_chat_history, load_relationship

client = TestClient(app)

def test_multi_user_isolation_and_modes():
    print("\n--- Starting Multi-User Isolation & Relationship Modes Test ---", flush=True)

    user_a = "test_user_alice"
    user_b = "test_user_bob"
    user_c = "test_user_charlie"

    # 1. Create Mentor for User A
    print("1. Creating Mentor companion for Alice...", flush=True)
    res_a = client.post(
        "/companion/create",
        headers={"X-User-Id": user_a},
        json={
            "name": "Prof. Alan",
            "gender": "Male",
            "age": 42,
            "relationship_mode": "mentor",
            "traits": ["Wise", "Disciplined"],
            "hobbies": ["Chess", "Reading"],
            "speaking_style": "Intelligent",
            "goal": "Help you master software engineering",
            "generate_avatar": False
        }
    )
    assert res_a.status_code == 200, f"Alice companion creation failed: {res_a.text}"
    print(f"Alice companion created: {res_a.json()['companion']['name']} | Mode: {res_a.json()['companion']['relationship_mode']}", flush=True)

    # 2. Create Lover for User B
    print("\n2. Creating Lover companion for Bob...", flush=True)
    res_b = client.post(
        "/companion/create",
        headers={"X-User-Id": user_b},
        json={
            "name": "Rose",
            "gender": "Female",
            "age": 21,
            "relationship_mode": "lover",
            "traits": ["Loving", "Sweet"],
            "hobbies": ["Music", "Art"],
            "speaking_style": "Sweet",
            "goal": "Cherish and love you always",
            "generate_avatar": False
        }
    )
    assert res_b.status_code == 200, f"Bob companion creation failed: {res_b.text}"
    print(f"Bob companion created: {res_b.json()['companion']['name']} | Mode: {res_b.json()['companion']['relationship_mode']}", flush=True)

    # 3. Create Friend for User C
    print("\n3. Creating Friend companion for Charlie...", flush=True)
    res_c = client.post(
        "/companion/create",
        headers={"X-User-Id": user_c},
        json={
            "name": "Sam",
            "gender": "Non-Binary",
            "age": 22,
            "relationship_mode": "friendship",
            "traits": ["Funny", "Loyal"],
            "hobbies": ["Gaming", "Anime"],
            "speaking_style": "Cheerful",
            "goal": "Be your gaming buddy",
            "generate_avatar": False
        }
    )
    assert res_c.status_code == 200, f"Charlie companion creation failed: {res_c.text}"
    print(f"Charlie companion created: {res_c.json()['companion']['name']} | Mode: {res_c.json()['companion']['relationship_mode']}", flush=True)

    # 4. Verify Data Isolation on GET /companion
    print("\n4. Verifying Companion Isolation across user headers...", flush=True)
    comp_a = client.get("/companion", headers={"X-User-Id": user_a}).json()
    comp_b = client.get("/companion", headers={"X-User-Id": user_b}).json()
    comp_c = client.get("/companion", headers={"X-User-Id": user_c}).json()

    assert comp_a["name"] == "Prof. Alan" and comp_a["relationship_mode"] == "mentor"
    assert comp_b["name"] == "Rose" and comp_b["relationship_mode"] == "lover"
    assert comp_c["name"] == "Sam" and comp_c["relationship_mode"] == "friendship"
    print("[PASS] Companion isolation verified! Each user gets their own companion.", flush=True)

    # 5. Send distinct chats and verify chat history isolation
    print("\n5. Testing Chat and History Isolation...", flush=True)
    with patch("chat_service.generate_speech", return_value={"url": "/static/audio/dummy.mp3", "cached": True}):
        chat_a = client.post(
            "/chat",
            headers={"X-User-Id": user_a},
            json={"message": "Can you help me organize my study schedule?"}
        ).json()
        print(f"Alice chat reply: {chat_a['reply'][:100]} ...", flush=True)

        chat_b = client.post(
            "/chat",
            headers={"X-User-Id": user_b},
            json={"message": "I missed you so much today sweetheart! Give me a big hug!"}
        ).json()
        print(f"Bob chat reply: {chat_b['reply'][:100]} ...", flush=True)

        chat_c = client.post(
            "/chat",
            headers={"X-User-Id": user_c},
            json={"message": "Hey buddy, are you ready to play some games tonight?"}
        ).json()
        print(f"Charlie chat reply: {chat_c['reply'][:100]} ...", flush=True)

    # Check histories
    hist_a = client.get("/history", headers={"X-User-Id": user_a}).json()
    hist_b = client.get("/history", headers={"X-User-Id": user_b}).json()
    hist_c = client.get("/history", headers={"X-User-Id": user_c}).json()

    assert len(hist_a) == 2, f"Alice expected 2 entries, got {len(hist_a)}"
    assert len(hist_b) == 2, f"Bob expected 2 entries, got {len(hist_b)}"
    assert len(hist_c) == 2, f"Charlie expected 2 entries, got {len(hist_c)}"

    assert "study schedule" in hist_a[0]["message"]
    assert "sweetheart" in hist_b[0]["message"]
    assert "games tonight" in hist_c[0]["message"]
    print("[PASS] Chat histories are 100% isolated! No data leakage between users.", flush=True)

    # 6. Mode Switch Test
    print("\n6. Testing Relationship Mode Switch on the fly...", flush=True)
    switch_res = client.post(
        "/companion/relationship-mode",
        headers={"X-User-Id": user_c},
        json={"mode": "mentor"}
    ).json()
    assert switch_res["success"] is True
    assert switch_res["companion"]["relationship_mode"] == "mentor"
    
    comp_c_updated = client.get("/companion", headers={"X-User-Id": user_c}).json()
    assert comp_c_updated["relationship_mode"] == "mentor"
    print("[PASS] Relationship Mode dynamically updated to Mentor for Charlie.", flush=True)

    print("\n==========================================", flush=True)
    print("ALL MULTI-USER & MODE TESTS PASSED SUCCESSFULLY!", flush=True)
    print("==========================================\n", flush=True)

if __name__ == "__main__":
    test_multi_user_isolation_and_modes()
