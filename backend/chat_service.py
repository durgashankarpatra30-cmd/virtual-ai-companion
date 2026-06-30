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
saved_data=load_companion()
user_memory = load_user_memory()
chat_history=load_chat_history()
relationship=load_relationship()
if saved_data:
    companion = Companion(
    saved_data["name"],
    saved_data["age"],
    saved_data["traits"],
    saved_data["hobbies"],
    saved_data["speaking_style"],
    saved_data["goal"]
)

def process_message(user_message):
    
    global chat_history
    global relationship

    chat_history.append({
        "role":"user",
        "message":user_message
    })
    
    
        
    relationship=update_relationship(relationship,user_message)  
    save_relationship(relationship)
    if should_save_memory(user_message):
        memory=extract_memory(user_message)
        
        if memory:
            user_memory.update(memory)
            save_user_memory(user_memory)

    prompt = build_prompt(
    companion,
    user_memory,
    chat_history,
    user_message,
    relationship
)

    #print(prompt)
    response = generate_ai_message(prompt)

    
    chat_history.append({
        "role":"assistant",
        "message":response

    })
    save_chat_history(chat_history)
    return response 
