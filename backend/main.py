from companion import Companion
from memory import save_companion,load_companion
saved_data = load_companion()
from memory import (
    save_companion,
    load_companion,
    save_user_memory,
    load_user_memory,
    save_chat_history,
    load_chat_history
)

user_memory = load_user_memory()
chat_history=load_chat_history()

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
        print("\n===== COMPANION CREATED =====")
        print("Name:", companion.name)
        print("Age:", companion.age)
        print("Traits:", companion.traits)
        print("Hobbies:", companion.hobbies)
        print("Speaking Style:", companion.speaking_style)
        print("Goal:", companion.goal)

while True:

    user_message = input("\nYou: ")
    chat_history.append({
        "role":"user",
        "message":user_message
    })

    if user_message.lower() == "exit":
        print("Good bye")
        break

    # MEMORY SAVE
    if "my favorite subject is" in user_message.lower():

        subject = user_message.split("is")[-1].strip()

        user_memory["favorite_subject"] = subject

        save_user_memory(user_memory)

        print(f"{companion.name}: I'll remember that.")

        continue

    # MEMORY RECALL
    if "what is my favorite subject" in user_message.lower():

        subject = user_memory.get(
            "favorite_subject",
            "I don't know yet."
        )

        print(
            f"{companion.name}: Your favorite subject is {subject}"
        )

        continue

    # NORMAL CHAT
    response = companion.generate_message(user_message)

    print(f"{companion.name}: {response}")
    chat_history.append({
        "role":"assistant",
        "message":response

    })
    save_chat_history(chat_history)
