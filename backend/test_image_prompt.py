from Image.image_prompt import build_image_prompt
from Image.image_generator import generate_companion_image, get_image_history
from models.companion import Companion


companion = Companion(
    "Aaru",
    19,
    ["Kind", "Sweet", "Caring"],
    ["Dancing", "Reading"],
    "Sweet",
    "Doctor"
)


print("\n" + "=" * 60)
print("GENERATING IMAGE PROMPT & TEST IMAGE")
print("=" * 60 + "\n")

prompt = build_image_prompt(companion)
print(f"Prompt:\n{prompt}\n")

print("Generating test image...")
try:
    result = generate_companion_image(companion, is_avatar=True)
    print(f"Successfully generated image!")
    print(f"URL: {result['url']}")
    print(f"Saved at: {result['filename']}")
except Exception as e:
    print(f"Image generation error: {e}")

print("\n" + "=" * 60)