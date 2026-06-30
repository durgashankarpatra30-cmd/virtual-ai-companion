
import json 
import ollama
IMPORTANT_KEYWORDS = [
    
    "favorite",
    "love",
    "hate",
    "goal",
    "dream",
    "birthday",
    "college",
    "job",
    "family",
    "friend",
    "hobby"
]
def should_save_memory(message):
    message=message.lower()
    for keyword in IMPORTANT_KEYWORDS:
        if keyword in message :
            return True
    return False    
def extract_memory(user_message):
    prompt = f"""
You are an information extraction engine.

Extract only long-term user facts.

Return ONLY valid JSON.

Do not explain anything.
Do not use markdown.
Do not write ```json.
Do not write sentences.

Examples:

Input:
My birthday is 21st December

Output:
{{"birthday":"21st December"}}

Input:
My favorite place is Shimla

Output:
{{"favorite_place":"Shimla"}}

Input:
Hello

Output:
{{}}

User message:
{user_message}
"""





    
    response = ollama.chat(
    model="llama3.2:3b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

    response_text = response["message"]["content"]

    response_text = response_text.replace("```json", "")
    response_text = response_text.replace("```", "")
    response_text = response_text.strip()

    try:
        memory = json.loads(response_text)
    except json.JSONDecodeError:
        memory={}    
    return memory
    
    

