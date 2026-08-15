class Companion:
    def __init__(
        self,
        name,
        age,
        traits,
        hobbies,
        speaking_style,
        goal,
        gender="Female",
        voice_id=None,
        voice_speed="+0%",
        voice_pitch="+0Hz"
    ):
        self.name = name
        self.age = age
        self.traits = traits if isinstance(traits, list) else [traits]
        self.hobbies = hobbies if isinstance(hobbies, list) else [hobbies]
        self.speaking_style = speaking_style
        self.goal = goal
        self.gender = gender
        self.voice_id = voice_id or ("en-US-GuyNeural" if str(gender).lower() in ["male", "man", "boy"] else "en-US-AriaNeural")
        self.voice_speed = voice_speed or "+0%"
        self.voice_pitch = voice_pitch or "+0Hz"

    def generate_message(self, message):
        if "hi" in message.lower():
            return f"Hello! My name is {self.name}"
        elif "how are you" in message.lower():
            return "I am fine. Thank you."
        elif "bye" in message.lower():
            return "See you later."
        elif "tell me about yourself" in message.lower():
            return (
                f"Hi! I am {self.name}. "
                f"I am {', '.join(self.traits)}. "
                f"My hobbies are {', '.join(self.hobbies)}. "
                f"My speaking style is {self.speaking_style}. "
                f"My goal is {self.goal}."
            )
        return "Tell me more about yourself"