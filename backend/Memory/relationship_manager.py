def update_relationship(relationship, user_message):

    # Increase message count
    relationship["total_messages"] += 1

    # Calculate friendship level
    relationship["friendship_level"] = (
        relationship["total_messages"] // 20
    )

    # Progress inside current level
    relationship["relationship_progress"] = (
        relationship["total_messages"] % 20
    ) * 5

    # Relationship stage
    level = relationship["friendship_level"]

    if level == 0:
        stage = "Stranger"

    elif level == 1:
        stage = "Acquaintance"

    elif level <= 3:
        stage = "Friend"

    elif level <= 5:
        stage = "Close Friend"

    elif level <= 10:
        stage = "Best Friend"

    else:
        stage = "Soulmate"

    relationship["relationship_stage"] = stage

    # Mood
    message = user_message.lower()

    if "thank" in message:
        relationship["current_mood"] = "Happy"

    elif "exam" in message:
        relationship["current_mood"] = "Supportive"

    elif "bye" in message:
        relationship["current_mood"] = "Sad"

    return relationship