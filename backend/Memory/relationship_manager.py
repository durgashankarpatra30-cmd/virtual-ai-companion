def update_relationship(relationship, user_message):
    # Ensure keys exist
    if "total_messages" not in relationship:
        relationship["total_messages"] = 0
    if "friendship_level" not in relationship:
        relationship["friendship_level"] = 1

    # Increase message count
    relationship["total_messages"] += 1

    # Calculate friendship/connection level (1 level per 12 messages)
    relationship["friendship_level"] = max(1, (relationship["total_messages"] // 12) + 1)

    # Progress inside current level (0% - 100%)
    relationship["relationship_progress"] = ((relationship["total_messages"] % 12) / 12) * 100

    # Relationship stage progression based on connection depth
    level = relationship["friendship_level"]
    message = user_message.lower()

    if level <= 1:
        stage = "New Companion"
    elif level <= 3:
        stage = "Close Companion"
    elif level <= 6:
        stage = "Romantic Partner"
    elif level <= 10:
        stage = "Passionate Love"
    else:
        stage = "Eternal Soulmate"

    # If user explicitly expresses love or deep intimacy, accelerate romantic bonding
    if any(k in message for k in ["love you", "my girlfriend", "my boyfriend", "my wife", "my husband", "my partner", "soulmate", "marry me", "darling"]):
        if level >= 2 and stage not in ["Passionate Love", "Eternal Soulmate"]:
            stage = "Romantic Partner"

    relationship["relationship_stage"] = stage

    import random
    # Dynamic feminine mood system with natural emotional shifts (clingy, teasing, sassy, shy, melty, pouting)
    if any(k in message for k in ["kiss", "smooch", "make out", "lips"]):
        mood_options = [
            "Deeply Passionate & Melty 💋",
            "Playfully Sassy & Teasing 😏",
            "Shy & Blushing 🙈",
            "Super Clingy & Needy 🥺"
        ]
        relationship["current_mood"] = random.choice(mood_options)
    elif any(k in message for k in ["love", "hug", "cuddle", "hold", "touch", "adore", "miss you", "sweetheart", "babe", "darling"]):
        mood_options = [
            "Super Clingy & Needy 🥺",
            "Deeply Loving & Affectionate 🥰",
            "Playfully Teasing & Coy 😏",
            "Warm & Cozy Cuddle Mode 🧸",
            "Playfully Pouting / Demanding Attention 😤"
        ]
        relationship["current_mood"] = random.choice(mood_options)
    elif any(k in message for k in ["why", "where", "late", "forgot", "busy", "who", "other"]):
        mood_options = [
            "Playfully Pouting & Jealous 😤",
            "Playfully Sassy & Sarcastic 😏",
            "Feisty & Demanding Attention 💅"
        ]
        relationship["current_mood"] = random.choice(mood_options)
    elif any(k in message for k in ["thank", "great", "happy", "yay", "awesome", "fun", "laugh", "lol", "haha"]):
        relationship["current_mood"] = random.choice(["Joyful & Playful ✨", "Giggling & Mischievous 😜"])
    elif any(k in message for k in ["sad", "depressed", "cry", "hurt", "tired", "stressed", "pain", "bad day", "lonely", "help"]):
        relationship["current_mood"] = "Warm & Deeply Comforting 🫂"
    elif any(k in message for k in ["bye", "goodbye", "good night", "gn", "sleep", "leaving"]):
        relationship["current_mood"] = random.choice(["Tender & Missing You 🌙", "Clingy - Don't Go Yet 🥺"])
    elif any(k in message for k in ["exam", "test", "work", "busy", "interview", "study"]):
        relationship["current_mood"] = "Encouraging & Proud Partner 💪"
    else:
        general_moods = [
            "Happy & Attentive 💕",
            "Playfully Teasing 😏",
            "Sweet & A Little Clingy 🥺",
            "Mischievous & Curious 🧐",
            "Tender & Loving 🥰"
        ]
        relationship["current_mood"] = random.choice(general_moods)

    return relationship