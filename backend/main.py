from models.companion import Companion
from Memory.memory import save_companion,load_companion
from Ai.ai_engine import build_prompt,generate_ai_message
from Memory.memory import (
    save_companion,
    load_companion,
    save_user_memory,
    load_user_memory,
    save_chat_history,
    load_chat_history,
    load_relationship,
    save_relationship
)
from Memory.memory_manager import should_save_memory,extract_memory
from Memory.relationship_manager import update_relationship
from chat_service import process_message
saved_data=load_companion()
user_memory = load_user_memory()
chat_history=load_chat_history()
relationship=load_relationship()

            


if saved_data:

    print(f"\nWelcome back! {saved_data['name']}")

    choice = input(
        "Use existing companion? (y/n): "
    )

    if choice.lower() == "y":

        companion = Companion(
            saved_data["name"],
            saved_data["age"],
            saved_data["traits"],
            saved_data["hobbies"],
            saved_data["speaking_style"],
            saved_data["goal"]
        )

        print("\nCompanion Loaded Successfully!")
        print("Name:", companion.name)

    else:
        name=input("Comapnion name : ")
        age=int(input("Enter companion's age : "))
        traits=(input("Enetr traits(Comma separated) : ")).split(',')
        hobbies=(input("Enter the hobbies of your Companion (Comma separated) : ")).split(",")
        speaking_style=input("Enter your Companion speaking style: ")
        goal=input("Enter the goal : ")
        companion = Companion(
    name,
    age,
    traits,
    hobbies,
    speaking_style,
    goal
)
        save_companion(companion)
        chat_history = []
        save_chat_history(chat_history)

        user_memory = {}
        save_user_memory(user_memory)

        relationship = {
    "friendship_level": 0,
    "current_mood": "neutral",
    "total_messages": 0
}
        save_relationship(relationship)
        print("\n===== COMPANION CREATED =====")
        print("Name:", companion.name)
        print("Age:", companion.age)
        print("Traits:", companion.traits)
        print("Hobbies:", companion.hobbies)
        print("Speaking Style:", companion.speaking_style)
        print("Goal:", companion.goal)

while True:
#Normal Chat
    user_message = input("\nYou: ")
    if user_message.lower()=="exit":
       
      print("Good Bye")
      break
    
        
    result = process_message(user_message)
    reply_text = result["reply"] if isinstance(result, dict) else result
    print(f"{companion.name}: {reply_text}")
    if isinstance(result, dict) and result.get("image"):
        print(f"[{companion.name} sent an image: {result['image']}]")

    
    