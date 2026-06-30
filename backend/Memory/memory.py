import json
import os
FILE_PATH="../data/companion.json"


BASE_DIR =os.path.dirname( os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILE_PATH = os.path.join(BASE_DIR, "data", "companion.json")

def save_companion(companion):

    data = {
        "name": companion.name,
        "age": companion.age,
        "traits": companion.traits,
        "hobbies": companion.hobbies,
        "speaking_style": companion.speaking_style,
        "goal": companion.goal
    }

    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)
def save_companion(companion):
    data = {
        "name": companion.name,
        "age": companion.age,
        "traits": companion.traits,
        "hobbies": companion.hobbies,
        "speaking_style": companion.speaking_style,
        "goal": companion.goal
    }
    with open(FILE_PATH,"w") as f :
        json.dump(data,f,indent=4)

def load_companion():

    if not os.path.exists(FILE_PATH):
        return None

    with open(FILE_PATH, "r") as f:
        return json.load(f)
USER_MEMORY_FILE=os.path.join(BASE_DIR,"data","user_memory.json")
def save_user_memory(memory):
    with open(USER_MEMORY_FILE,"w") as f:
        json.dump(memory,f,indent=4)
def load_user_memory():
    if not os.path.exists(USER_MEMORY_FILE):
        return {}
    with open(USER_MEMORY_FILE,"r") as f:
        return json.load(f)


CHAT_HISTORY_FILE = os.path.join(
    BASE_DIR,
    "data",
    "chat_history.json"
)

def load_chat_history():

    if not os.path.exists(CHAT_HISTORY_FILE):
        return []

    with open(CHAT_HISTORY_FILE, "r") as f:
        return json.load(f)

def save_chat_history(history):

    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
RELATIONSHIP_FILE=os.path.join(BASE_DIR,"data","relationship.json")   
def load_relationship():
    if not os.path.exists(RELATIONSHIP_FILE):
        return {
            "friendship_level": 1,
            "days_talked": 1,
            "total_messages": 0,
            "favorite_topics": []
        }     
    with open(RELATIONSHIP_FILE,"r") as f:
        return json.load(f)
def save_relationship(data):
    with open(RELATIONSHIP_FILE,"w") as f:
        json.dump(data,f,indent=4)  