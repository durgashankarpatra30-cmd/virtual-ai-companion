class Companion:
    def __init__(
        self,
        name,
        age,
        traits,
        hobbies,
        speaking_style,
        goal
    ):
        self.name = name
        self.age = age
        self.traits = traits
        self.hobbies = hobbies
        self.speaking_style = speaking_style
        self.goal = goal
    def generate_message(self,message):

        if "hi" in message.lower():
         return (f"Hello! My name is {self.name}")
        elif  "how are you" in message.lower():
         return "I am fine.Thank you." 
        elif "bye" in message.lower():
         return "See you later." 
        elif "tell me about yourself" in message:

         return (
        f"Hi! I am {self.name}. "
        f"I am {', '.join(self.traits)}. "
        f"My hobbies are {', '.join(self.hobbies)}. "
        f"My speaking style is {self.speaking_style}. "
        f"My goal is {self.goal}."
    )
        return "Tell me more about yourself" 


        