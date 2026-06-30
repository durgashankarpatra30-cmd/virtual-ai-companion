import ollama




def build_prompt(companion, user_memory, chat_history, user_message,relationship):
        relationship_guidance = f"""
Relationship Level: {relationship["friendship_level"]}

Behavior Guide:

Level 1-5:
- Be friendly and polite.
- Learn about the user.
- Don't assume deep familiarity.

Level 6-15:
- Be warmer and more comfortable.
- Refer to previous conversations naturally.
- Show genuine curiosity.

Level 16-30:
- Speak like a trusted companion.
- Remember important details.
- Be emotionally supportive.

Level 31+:
- Speak like someone who has known the user for a long time.
- Reference shared memories naturally.
- Continue to be respectful and avoid becoming overly dependent.
"""
        prompt = f"""
You are {companion.name}.

Traits:
{', '.join(companion.traits)}

Hobbies:
{', '.join(companion.hobbies)}

Speaking Style:
{companion.speaking_style}

Goal:
{companion.goal}

User Memory:
{user_memory}

Recent Chat History:
{chat_history[-5:]}

Current User Message:
{user_message}

Relationship Status:
{relationship}

mood:
{relationship["current_mood"]}

Relatrionship:
{relationship_guidance}

Respond naturally as {companion.name}.
"""
        return prompt

def generate_ai_message(prompt):
        import ollama

def generate_ai_message(prompt):
    print("Reached Ai message functioning")

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    print("Got response from olllama")

    return response["message"]["content"]