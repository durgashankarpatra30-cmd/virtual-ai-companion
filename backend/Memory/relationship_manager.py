import random

def update_relationship(relationship, user_message, companion=None):
    """
    Updates the relationship progress, levels, stages, and dynamic mood based on the active relationship mode:
    - friendship: Informal, cheerful, loyal friend with healthy intimacy boundaries.
    - mentor: Strictly official, formal, professional, wise guidance & coaching.
    - lover: Intimate, romantic, affectionate, clingy and passionate partner.
    """
    # Ensure keys exist
    if "total_messages" not in relationship:
        relationship["total_messages"] = 0
    if "friendship_level" not in relationship:
        relationship["friendship_level"] = 1

    mode = relationship.get("relationship_mode")
    if not mode and companion:
        mode = getattr(companion, "relationship_mode", "friendship")
    mode = (mode or "friendship").lower().strip()
    relationship["relationship_mode"] = mode

    # Increase message count
    relationship["total_messages"] += 1

    # Calculate level (1 level per 10 messages)
    level = max(1, (relationship["total_messages"] // 10) + 1)
    relationship["friendship_level"] = level

    # Progress inside current level (0% - 100%)
    relationship["relationship_progress"] = ((relationship["total_messages"] % 10) / 10) * 100

    message = user_message.lower()

    # -------------------------------------------------------------
    # 1. FRIENDSHIP MODE
    # -------------------------------------------------------------
    if mode == "friendship":
        if level <= 1:
            stage = "New Acquaintance"
        elif level <= 3:
            stage = "Casual Friend"
        elif level <= 6:
            stage = "Close Friend"
        elif level <= 10:
            stage = "Best Friend / Confidante"
        else:
            stage = "Inseparable Soul Buddy"

        relationship["relationship_stage"] = stage

        # Mood system for Friendship
        if any(k in message for k in ["sad", "depressed", "cry", "hurt", "tired", "stressed", "pain", "bad day", "lonely", "help"]):
            relationship["current_mood"] = "Warm & Comforting Friend 🫂"
        elif any(k in message for k in ["exam", "test", "work", "busy", "interview", "study", "code", "project"]):
            relationship["current_mood"] = "Cheering You On! 🥳"
        elif any(k in message for k in ["thank", "great", "happy", "yay", "awesome", "fun", "laugh", "lol", "haha"]):
            relationship["current_mood"] = random.choice(["Upbeat & Laughing 😆", "Joyful & Energetic ✨"])
        elif any(k in message for k in ["game", "music", "movie", "anime", "play", "hangout", "trip", "fun"]):
            relationship["current_mood"] = random.choice(["Hyped & Excited 🎮", "Chill & Relaxed ☕"])
        elif any(k in message for k in ["bye", "goodbye", "good night", "gn", "sleep", "leaving"]):
            relationship["current_mood"] = "Peaceful & Catch Ya Later 🌙"
        else:
            friend_moods = [
                "Upbeat & Energetic 😄",
                "Relaxed & Chilling ☕",
                "Curious & Chatty 🧐",
                "Supportive & Loyal 🤝",
                "Playfully Bantering 😜",
                "Thoughtful & In Good Spirits ✨"
            ]
            relationship["current_mood"] = random.choice(friend_moods)

    # -------------------------------------------------------------
    # 2. MENTOR MODE (Strictly Official & Formal)
    # -------------------------------------------------------------
    elif mode == "mentor":
        if level <= 1:
            stage = "New Mentee"
        elif level <= 3:
            stage = "Guided Apprentice"
        elif level <= 6:
            stage = "Trusted Protégé"
        elif level <= 10:
            stage = "Respected Colleague"
        else:
            stage = "Master & Lifelong Advisor"

        relationship["relationship_stage"] = stage

        # Mood system for Mentor
        if any(k in message for k in ["stuck", "doubt", "fail", "hard", "problem", "difficult", "confused", "stress"]):
            relationship["current_mood"] = "Analytical & Constructive Guide 🧭"
        elif any(k in message for k in ["finished", "done", "succeeded", "passed", "solved", "won", "achieved"]):
            relationship["current_mood"] = "Proud of Your Growth 🌟"
        elif any(k in message for k in ["goal", "plan", "future", "career", "study", "learning", "code", "work"]):
            relationship["current_mood"] = "Focused & Strategic 🎯"
        elif any(k in message for k in ["bye", "goodbye", "good night", "gn", "leaving"]):
            relationship["current_mood"] = "Encouraging Rest & Focus 🌙"
        else:
            mentor_moods = [
                "Focused & Analytical 🎯",
                "Encouraging & Motivated 🚀",
                "Wise & Reflective 📚",
                "Constructive & Direct ✍️",
                "Thoughtful & Strategic 🧭"
            ]
            relationship["current_mood"] = random.choice(mentor_moods)

    # -------------------------------------------------------------
    # 3. LOVER MODE (Romantic, Affectionate & Cozy)
    # -------------------------------------------------------------
    else:  # 'lover'
        if level <= 1:
            stage = "Sweet Spark"
        elif level <= 3:
            stage = "Dating & Romance"
        elif level <= 6:
            stage = "Devoted Lover"
        elif level <= 10:
            stage = "Passionate Soulmate"
        else:
            stage = "Eternal Partner"

        if any(k in message for k in ["love you", "my girlfriend", "my boyfriend", "my wife", "my husband", "my partner", "soulmate", "marry me", "darling"]):
            if level >= 2 and stage not in ["Passionate Soulmate", "Eternal Partner"]:
                stage = "Devoted Lover"

        relationship["relationship_stage"] = stage

        # Mood system for Lover
        if any(k in message for k in ["kiss", "smooch", "make out", "lips"]):
            relationship["current_mood"] = random.choice([
                "Deeply Passionate & Melty 💋",
                "Playfully Sassy & Teasing 😏",
                "Shy & Blushing 🙈",
                "Super Clingy & Needy 🥺"
            ])
        elif any(k in message for k in ["love", "hug", "cuddle", "hold", "touch", "adore", "miss you", "sweetheart", "babe", "darling"]):
            relationship["current_mood"] = random.choice([
                "Super Clingy & Needy 🥺",
                "Deeply Loving & Affectionate 🥰",
                "Playfully Teasing & Coy 😏",
                "Warm & Cozy Cuddle Mode 🧸"
            ])
        elif any(k in message for k in ["why", "where", "late", "forgot", "busy", "who", "other"]):
            relationship["current_mood"] = random.choice([
                "Playfully Pouting & Jealous 😤",
                "Playfully Sassy 😏",
                "Feisty & Demanding Attention 💅"
            ])
        elif any(k in message for k in ["sad", "depressed", "cry", "hurt", "tired", "stressed", "pain", "bad day", "lonely", "help"]):
            relationship["current_mood"] = "Warm & Deeply Comforting Hug 🫂"
        elif any(k in message for k in ["bye", "goodbye", "good night", "gn", "sleep", "leaving"]):
            relationship["current_mood"] = random.choice(["Tender & Missing You 🌙", "Clingy - Don't Go Yet 🥺"])
        else:
            lover_moods = [
                "Happy & Attentive 💕",
                "Playfully Teasing 😏",
                "Sweet & A Little Clingy 🥺",
                "Tender & Loving 🥰"
            ]
            relationship["current_mood"] = random.choice(lover_moods)

    return relationship