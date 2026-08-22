import sys
import os

# Fix SSL on Python 3.14 Windows
os.environ.pop("SSLKEYLOGFILE", None)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from models.companion import Companion
from Image.image_prompt import build_image_prompt, get_character_seed
from Image.image_generator import generate_companion_image

def test_photoreal_image_generation():
    print("Testing Photoreal Image Prompt & Generation...", flush=True)

    companion = Companion(
        name="Aaru",
        age=20,
        traits=["Sweet", "Kind"],
        hobbies=["Dancing", "Reading"],
        speaking_style="Sweet",
        goal="Be your best friend",
        gender="Female",
        relationship_mode="lover"
    )

    seed = get_character_seed(companion, user_id="test_user_photoreal")
    print(f"Character seed for {companion.name}: {seed}", flush=True)

    prompt = build_image_prompt(
        companion,
        custom_scene="taking a smiling selfie at a cozy cafe",
        is_selfie=True,
        user_id="test_user_photoreal"
    )
    print("\nGenerated High-Fidelity Prompt:\n", prompt, flush=True)

    assert "Raw 8k color portrait photograph" in prompt
    assert "Aaru" in prompt
    assert "Sony A7R V" in prompt or "selfie angle" in prompt
    assert "Ultra-photorealistic" in prompt

    print("\n[PASS] Photoreal prompt builder verified successfully!", flush=True)

if __name__ == "__main__":
    test_photoreal_image_generation()
