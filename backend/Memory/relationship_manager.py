def update_relationship(
    relationship,
    user_message
):

    relationship["total_messages"] += 1

    if relationship["total_messages"] % 20 == 0:
        relationship["friendship_level"] += 1

    if "thank" in user_message.lower():
        relationship["current_mood"] = "Happy"

    elif "exam" in user_message.lower():
        relationship["current_mood"] = "Supportive"

    elif "bye" in user_message.lower():
        relationship["current_mood"] = "Sad"

    return relationship