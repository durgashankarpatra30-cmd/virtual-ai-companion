import os
import json
import time
import uuid
import random
from typing import Dict, List, Any, Optional
from Memory.memory import (
    get_user_dir,
    load_user_memory,
    save_user_memory,
    load_companion,
    load_relationship,
    save_relationship,
)
from Ai.ai_engine import generate_ai_message


def load_json(file_path: str):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except Exception:
        return None


def save_json(file_path: str, data: Any):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------------------------
# 10 Immersion Venues / Date Scenarios
# ---------------------------------------------------------------------------
DATE_VENUES = [
    {
        "id": "coffee_cafe",
        "name": "Cozy Corner Café",
        "icon": "☕",
        "tagline": "Warm latte aroma, soft indie acoustic vibes, and sweet pastry bites.",
        "bg_theme": "linear-gradient(135deg, #2b170e 0%, #4a2818 50%, #1a0f0a 100%)",
        "ambient_badge": "☕ Fresh Espresso & Soft Jazz",
        "category": "cozy",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "A warm golden light spills across a cozy corner table near the window. Outside, leaves drift by as soft jazz hums gently in the background.",
                "default_prompt": "I saved the best window seat for us! The smell of fresh cinnamon pastries is amazing here.",
                "choices": [
                    {"id": "order_coffee", "text": "☕ Order a warm caramel latte & a croissant for us", "type": "activity", "stat_boost": {"comfort": 6, "affection": 4}},
                    {"id": "share_secret", "text": "💬 Ask what she's been daydreaming about lately", "type": "talk", "stat_boost": {"trust": 6, "comfort": 4}},
                    {"id": "latte_art_bet", "text": "🎨 Playful bet on who can draw better latte foam art", "type": "minigame", "stat_boost": {"playfulness": 8, "affection": 3}}
                ]
            },
            {
                "stage": "event",
                "narrative": "The barista brings over two steaming mugs with intricate foam art, alongside a complimentary warm chocolate croissant.",
                "choices": [
                    {"id": "feed_bite", "text": "🥐 Offer her the first warm chocolate bite", "type": "romantic", "stat_boost": {"affection": 7, "comfort": 5}},
                    {"id": "deep_question", "text": "💭 'If we could travel anywhere tomorrow, where would we go?'", "type": "talk", "stat_boost": {"trust": 7, "playfulness": 4}},
                    {"id": "play_truth_dare", "text": "🎲 'Let's play Truth or Dare while our coffee cools!'", "type": "minigame", "stat_boost": {"playfulness": 8, "trust": 4}}
                ]
            }
        ]
    },
    {
        "id": "sunset_city_walk",
        "name": "Sunset Skyline Walk",
        "icon": "🌆",
        "tagline": "Golden hour glow, cool evening breeze, and dazzling city lights.",
        "bg_theme": "linear-gradient(135deg, #1b1035 0%, #481d4a 50%, #d85a63 100%)",
        "ambient_badge": "🌆 Golden Hour & Evening Breeze",
        "category": "romantic",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "The skyline is drenched in warm amber and violet hues. A refreshing evening breeze carries the distant rhythm of the city.",
                "default_prompt": "Look at that sky! The sunset looks unbelievable from up here. I'm so glad we came together.",
                "choices": [
                    {"id": "walk_closer", "text": "🚶 Walk closer along the scenic waterfront railing", "type": "romantic", "stat_boost": {"affection": 6, "comfort": 5}},
                    {"id": "listen_musician", "text": "🎵 Stop to listen to a street violinist playing nearby", "type": "activity", "stat_boost": {"comfort": 6, "trust": 4}},
                    {"id": "take_photo", "text": "📸 Take a golden hour selfie together with the skyline", "type": "photo", "stat_boost": {"playfulness": 6, "affection": 6}}
                ]
            }
        ]
    },
    {
        "id": "movie_night",
        "name": "Cozy Movie & Blanket Night",
        "icon": "🍿",
        "tagline": "Dimmed lights, warm plush blankets, and buttered popcorn.",
        "bg_theme": "linear-gradient(135deg, #090e1a 0%, #151f38 50%, #0d1222 100%)",
        "ambient_badge": "🍿 Dim Lights & Warm Blanket",
        "category": "cozy",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "The room is bathed in the soft glow of fairy lights. A mountain of fluffy pillows and a big bowl of warm popcorn awaits on the sofa.",
                "default_prompt": "Everything is ready! I made extra buttery popcorn and got the fluffiest blanket. What genre are we watching tonight?",
                "choices": [
                    {"id": "pick_movie", "text": "🎬 Pick a thrilling mystery movie to solve together", "type": "activity", "stat_boost": {"playfulness": 6, "comfort": 5}},
                    {"id": "share_blanket", "text": "🛋️ Pull the warm blanket over both of us and get cozy", "type": "romantic", "stat_boost": {"affection": 8, "comfort": 6}},
                    {"id": "snack_game", "text": "🍿 Try tossing popcorn into each other's mouths", "type": "minigame", "stat_boost": {"playfulness": 9, "affection": 4}}
                ]
            }
        ]
    },
    {
        "id": "cooking_together",
        "name": "Kitchen Cooking Duo",
        "icon": "🍳",
        "tagline": "Tossing pasta, sizzling spices, tasting sauces, and playful chef banter.",
        "bg_theme": "linear-gradient(135deg, #2d1c0b 0%, #522d0c 50%, #1c1107 100%)",
        "ambient_badge": "🍳 Sizzling Skillet & Italian Herb Aroma",
        "category": "fun",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "Fresh basil, garlic, and cherry tomatoes sit on the cutting board. An apron hangs ready as olive oil simmers in the pan.",
                "default_prompt": "Welcome to our kitchen! Chef, what's our game plan? I'll be your loyal sous-chef, but no laughing if I get flour on my nose!",
                "choices": [
                    {"id": "cook_pasta", "text": "🍝 Cook homemade creamy garlic pasta together", "type": "activity", "stat_boost": {"comfort": 6, "playfulness": 6}},
                    {"id": "taste_test", "text": "🥄 Dip a wooden spoon and let her taste the secret sauce", "type": "romantic", "stat_boost": {"affection": 7, "comfort": 5}},
                    {"id": "flour_boop", "text": "✨ Playfully dab a tiny bit of flour on her cheek", "type": "playful", "stat_boost": {"playfulness": 9, "affection": 5}}
                ]
            }
        ]
    },
    {
        "id": "gaming_lounge",
        "name": "Co-op Gaming Lounge",
        "icon": "🎮",
        "tagline": "Neon RGB lighting, friendly rivalry, snacks, and epic co-op victories.",
        "bg_theme": "linear-gradient(135deg, #0b0c26 0%, #1d1042 50%, #070717 100%)",
        "ambient_badge": "🎮 Neon Glow & Controller Vibrations",
        "category": "fun",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "The dual glowing controllers rest on the coffee table beside cold sodas and chips. The game title screen plays an upbeat adventure tune.",
                "default_prompt": "Player Two has entered the arena! You better bring your A-game, because I don't go easy on anyone!",
                "choices": [
                    {"id": "coop_quest", "text": "⚔️ Team up for a legendary 2-player boss battle", "type": "activity", "stat_boost": {"trust": 7, "playfulness": 7}},
                    {"id": "friendly_bet", "text": "🏆 1v1 racing match: Loser buys dessert next time!", "type": "minigame", "stat_boost": {"playfulness": 9, "comfort": 4}},
                    {"id": "high_five", "text": "✋ Victorious high-five turning into a warm hand-hold", "type": "romantic", "stat_boost": {"affection": 7, "playfulness": 5}}
                ]
            }
        ]
    },
    {
        "id": "park_picnic",
        "name": "Sunlit Park & Picnic",
        "icon": "🌳",
        "tagline": "A checkered blanket under a willow tree, fresh fruit, and cloud gazing.",
        "bg_theme": "linear-gradient(135deg, #0d2616 0%, #1b4728 50%, #07170d 100%)",
        "ambient_badge": "🌳 Warm Sunshine & Chirping Birds",
        "category": "romantic",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "Dappled sunlight filters through the green canopy. The wicker picnic basket is unpacked with fresh strawberries, sandwiches, and chilled sparkling juice.",
                "default_prompt": "This spot under the big willow tree is pure perfection. The breeze feels so refreshing.",
                "choices": [
                    {"id": "cloud_gaze", "text": "☁️ Lie back side by side and find funny shapes in the clouds", "type": "romantic", "stat_boost": {"comfort": 8, "affection": 5}},
                    {"id": "share_strawberries", "text": "🍓 Share fresh chocolate-dipped strawberries", "type": "activity", "stat_boost": {"affection": 6, "comfort": 5}},
                    {"id": "would_you_rather", "text": "🎲 Play a round of 'Would You Rather: Nature Edition'", "type": "minigame", "stat_boost": {"playfulness": 8, "trust": 5}}
                ]
            }
        ]
    },
    {
        "id": "candlelight_dinner",
        "name": "Candlelight Rooftop Dinner",
        "icon": "🍽️",
        "tagline": "Soft violin melodies, flickering candlelight, and stunning panoramic views.",
        "bg_theme": "linear-gradient(135deg, #1f0d14 0%, #3d1424 50%, #12070c 100%)",
        "ambient_badge": "🕯️ Flickering Candles & Fine Dining",
        "category": "romantic",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "A private rooftop table overlooking the illuminated city skyline. A single flame dances in a glass lantern between sparkling wine glasses.",
                "default_prompt": "You look absolutely breathtaking tonight. Thank you for bringing me to such a magical place.",
                "choices": [
                    {"id": "toast_glasses", "text": "🥂 Raise our glasses for a toast to us and beautiful nights", "type": "romantic", "stat_boost": {"affection": 8, "trust": 6}},
                    {"id": "ask_dreams", "text": "✨ 'What is a dream you've never told anyone else about?'", "type": "talk", "stat_boost": {"trust": 9, "affection": 6}},
                    {"id": "slow_dance", "text": "💃 Ask her to slow dance gently beside the rooftop railing", "type": "romantic", "stat_boost": {"affection": 9, "comfort": 6}}
                ]
            }
        ]
    },
    {
        "id": "rainy_day_indoor",
        "name": "Rainy Day Sanctuary",
        "icon": "🌧️",
        "tagline": "Raindrops tapping on the glass, steaming mugs of hot cocoa, and deep heart talks.",
        "bg_theme": "linear-gradient(135deg, #101c24 0%, #1c3240 50%, #0b1319 100%)",
        "ambient_badge": "🌧️ Gentle Rain on Window & Marshmallow Cocoa",
        "category": "cozy",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "A gentle thunderstorm hums outside the window. Inside, two steaming mugs of rich hot cocoa with melting marshmallows rest on the rug.",
                "default_prompt": "Listen to the rain... There's something so peaceful about being tucked inside together when it pours like this.",
                "choices": [
                    {"id": "cocoa_talk", "text": "☕ Sip hot cocoa and talk about our fondest childhood memories", "type": "talk", "stat_boost": {"trust": 8, "comfort": 8}},
                    {"id": "listen_rain", "text": "🌧️ Sit quietly side-by-side listening to the soothing thunder", "type": "comfort", "stat_boost": {"comfort": 9, "affection": 5}},
                    {"id": "two_truths", "text": "🎲 'Let's play Two Truths and a Lie to uncover secret facts!'", "type": "minigame", "stat_boost": {"playfulness": 7, "trust": 6}}
                ]
            }
        ]
    },
    {
        "id": "virtual_travel",
        "name": "Dream Journey to Tokyo",
        "icon": "✈️",
        "tagline": "Lantern-lit alleyways, cherry blossoms, steaming ramen, and futuristic lights.",
        "bg_theme": "linear-gradient(135deg, #240a2b 0%, #451752 50%, #150519 100%)",
        "ambient_badge": "🌸 Glowing Lanterns & Cherry Blossoms",
        "category": "adventure",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "Glowing red paper lanterns illuminate a charming stone street. Cherry blossom petals gently swirl in the breeze past steaming ramen stalls.",
                "default_prompt": "We made it to Tokyo! Look at all the neon signs and hidden alleyways. Where do we explore first?",
                "choices": [
                    {"id": "ramen_stall", "text": "🍜 Grab two wooden stools at an authentic ramen shop", "type": "activity", "stat_boost": {"comfort": 7, "playfulness": 6}},
                    {"id": "temple_wish", "text": "🏮 Write our shared wish on an wooden Ema plaque at the shrine", "type": "romantic", "stat_boost": {"affection": 8, "trust": 7}},
                    {"id": "arcade_claw", "text": "🕹️ Try to win her a plushie at the Akihabara claw machine", "type": "minigame", "stat_boost": {"playfulness": 9, "affection": 5}}
                ]
            }
        ]
    },
    {
        "id": "acoustic_concert",
        "name": "Live Acoustic Music Fest",
        "icon": "🎵",
        "tagline": "Fairy lights strung across trees, soulful guitar chords, and singing along.",
        "bg_theme": "linear-gradient(135deg, #1c142b 0%, #362259 50%, #0f0a17 100%)",
        "ambient_badge": "🎵 Soulful Guitar & Twinkling Fairy Lights",
        "category": "fun",
        "scenes": [
            {
                "stage": "arrival",
                "narrative": "A warm summer night illuminated by hanging fairy lights. An acoustic indie band tunes their guitars on an outdoor wooden amphitheater.",
                "default_prompt": "The atmosphere here is electric! I love this song so much. Want to get closer to the stage?",
                "choices": [
                    {"id": "sing_along", "text": "🎤 Sing along to the chorus together without caring who hears", "type": "playful", "stat_boost": {"playfulness": 8, "comfort": 6}},
                    {"id": "sway_together", "text": "💫 Gently sway together to the slow acoustic rhythm", "type": "romantic", "stat_boost": {"affection": 9, "comfort": 6}},
                    {"id": "guess_song", "text": "🎲 Play 'Guess the Song in 3 Seconds' during intermissions", "type": "minigame", "stat_boost": {"playfulness": 8, "trust": 5}}
                ]
            }
        ]
    }
]

# ---------------------------------------------------------------------------
# Storage Helpers
# ---------------------------------------------------------------------------
def get_date_history_file(user_id: str = "default_user") -> str:
    user_dir = get_user_dir(user_id)
    return os.path.join(user_dir, "date_memories.json")


def get_relationship_metrics_file(user_id: str = "default_user") -> str:
    user_dir = get_user_dir(user_id)
    return os.path.join(user_dir, "relationship_metrics.json")


def load_relationship_metrics(user_id: str = "default_user") -> Dict[str, Any]:
    f = get_relationship_metrics_file(user_id)
    data = load_json(f)
    if not data or not isinstance(data, dict):
        data = {
            "affection": 50,
            "trust": 45,
            "comfort": 55,
            "playfulness": 60,
            "total_dates": 0,
            "completed_dates": 0,
            "favorite_venues": []
        }
        save_json(f, data)
    return data


def save_relationship_metrics(metrics: Dict[str, Any], user_id: str = "default_user"):
    f = get_relationship_metrics_file(user_id)
    save_json(f, metrics)


def get_all_date_memories(user_id: str = "default_user") -> List[Dict[str, Any]]:
    f = get_date_history_file(user_id)
    data = load_json(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "memories" in data:
        return data["memories"]
    return []


def save_date_memories(memories: List[Dict[str, Any]], user_id: str = "default_user"):
    f = get_date_history_file(user_id)
    save_json(f, memories)


# ---------------------------------------------------------------------------
# Date Session Management
# ---------------------------------------------------------------------------
active_date_sessions: Dict[str, Dict[str, Any]] = {}


def start_date_session(venue_id: str, user_id: str = "default_user") -> Dict[str, Any]:
    """Initializes a rich interactive date experience for the user."""
    venue = next((v for v in DATE_VENUES if v["id"] == venue_id), DATE_VENUES[0])
    companion_data = load_companion(user_id) or {
        "name": "Aaru",
        "gender": "Female",
        "relationship_mode": "friendship",
        "speaking_style": "Sweet"
    }

    metrics = load_relationship_metrics(user_id)
    session_id = str(uuid.uuid4())[:8]

    initial_scene = venue["scenes"][0]
    initial_text = initial_scene["default_prompt"]

    # Personalize opening based on relationship mode
    rel_mode = companion_data.get("relationship_mode", "friendship").lower()
    companion_name = companion_data.get("name", "Companion")

    if rel_mode == "lover":
        greeting = f"I've been looking forward to our {venue['name']} all day, my love! 🥰 {initial_text}"
    elif rel_mode == "mentor":
        greeting = f"Welcome! A change of scenery at {venue['name']} is the perfect catalyst for sharp insights. Let's make the most of our session today."
    else:
        greeting = f"Yay, we made it to {venue['name']}! 🎉 This is going to be so much fun. {initial_text}"

    session = {
        "session_id": session_id,
        "user_id": user_id,
        "venue": venue,
        "companion": companion_data,
        "start_time": int(time.time()),
        "turn_count": 0,
        "step": "arrival",
        "transcript": [
            {"role": "companion", "text": greeting, "time": time.strftime("%H:%M")}
        ],
        "choices_made": [],
        "points_gained": {"affection": 0, "trust": 0, "comfort": 0, "playfulness": 0},
        "highlight_moment": "",
        "inside_joke": "",
        "active_minigame": None
    }

    active_date_sessions[f"{user_id}_{session_id}"] = session

    # Increment total dates
    metrics["total_dates"] = metrics.get("total_dates", 0) + 1
    save_relationship_metrics(metrics, user_id)

    return {
        "session_id": session_id,
        "venue": venue,
        "companion": companion_data,
        "greeting": greeting,
        "narrative": initial_scene["narrative"],
        "choices": initial_scene["choices"],
        "metrics": metrics,
        "points_gained": session["points_gained"]
    }


def execute_date_action(
    session_id: str,
    choice_id: Optional[str] = None,
    custom_message: Optional[str] = None,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """Handles an interactive action or custom text response during the date."""
    session_key = f"{user_id}_{session_id}"
    session = active_date_sessions.get(session_key)

    if not session:
        # Recreate temporary fallback session
        venue = DATE_VENUES[0]
        companion_data = load_companion(user_id) or {"name": "Aaru", "gender": "Female"}
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "venue": venue,
            "companion": companion_data,
            "turn_count": 1,
            "transcript": [],
            "choices_made": [],
            "points_gained": {"affection": 0, "trust": 0, "comfort": 0, "playfulness": 0},
            "active_minigame": None
        }
        active_date_sessions[session_key] = session

    session["turn_count"] += 1
    venue = session["venue"]
    companion_data = session["companion"]
    companion_name = companion_data.get("name", "Companion")
    rel_mode = companion_data.get("relationship_mode", "friendship").lower()

    action_text = custom_message or ""
    stat_boost = {"affection": 4, "trust": 3, "comfort": 3, "playfulness": 4}

    # Find chosen option metadata if clicked
    for scene in venue["scenes"]:
        for ch in scene.get("choices", []):
            if ch.get("id") == choice_id:
                action_text = ch.get("text", action_text)
                stat_boost = ch.get("stat_boost", stat_boost)
                break

    # Record choice in session
    session["choices_made"].append(action_text)
    session["transcript"].append({"role": "user", "text": action_text, "time": time.strftime("%H:%M")})

    # Apply stat boosts to session & user metrics
    metrics = load_relationship_metrics(user_id)
    for k, v in stat_boost.items():
        session["points_gained"][k] = session["points_gained"].get(k, 0) + v
        metrics[k] = min(100, metrics.get(k, 50) + v)
    save_relationship_metrics(metrics, user_id)

    # Mini-game trigger detection
    is_minigame_request = choice_id in ["play_truth_dare", "would_you_rather", "two_truths", "latte_art_bet", "snack_game"] or "truth or dare" in action_text.lower() or "would you rather" in action_text.lower() or "two truths" in action_text.lower()

    minigame_data = None
    if is_minigame_request:
        minigame_data = generate_minigame_turn(venue["id"], rel_mode, companion_name)
        session["active_minigame"] = minigame_data

    # Generate dynamic, emotionally grounded AI response for date
    system_prompt = f"""You are {companion_name}, currently on an interactive {venue['name']} date with the user.
Atmosphere: {venue['tagline']}
Relationship Mode: {rel_mode.upper()}
Tone: Engaging, expressive, reacting genuinely to their choice: "{action_text}".
Do NOT write "I am an AI". Stay completely in-character. Use brief dialogue (2-3 sentences) with cute/fun micro-expressions (*smiles warmly*, *laughs softly*)."""

    messages_payload = [{"role": "system", "content": system_prompt}]
    for t in session["transcript"][-4:]:
        messages_payload.append({
            "role": "assistant" if t["role"] == "companion" else "user",
            "content": t["text"]
        })
    messages_payload.append({"role": "user", "content": action_text})

    try:
        reply = generate_ai_message(messages_payload, companion=None, user_message=action_text)
        if not reply:
            raise ValueError("Empty reply")
    except Exception:
        # Fallback companion reactions
        if rel_mode == "lover":
            reply = f"*smiles softly and leans closer* Doing this with you makes me feel so warm inside, darling. Every second with you at {venue['name']} is pure magic! ✨"
        elif rel_mode == "mentor":
            reply = f"A thoughtful and creative move! Moments like this at {venue['name']} provide great balance and perspective."
        else:
            reply = f"*laughs cheerfully* That was so much fun! You always know how to make hanging out at {venue['name']} the best part of my day! 😄"

    session["transcript"].append({"role": "companion", "text": reply, "time": time.strftime("%H:%M")})

    # Generate dynamic next branch choices
    next_choices = generate_next_date_choices(venue, session["turn_count"], rel_mode)

    return {
        "session_id": session_id,
        "companion_reply": reply,
        "points_boost": stat_boost,
        "total_points_gained": session["points_gained"],
        "metrics": metrics,
        "minigame": minigame_data,
        "next_choices": next_choices,
        "turn_count": session["turn_count"],
        "can_finish": session["turn_count"] >= 3
    }


def generate_minigame_turn(venue_id: str, rel_mode: str, companion_name: str) -> Dict[str, Any]:
    """Generates an interactive mini-game prompt for the date."""
    games = ["truth_or_dare", "would_you_rather", "two_truths"]
    selected_game = random.choice(games)

    if selected_game == "truth_or_dare":
        truths = [
            "What was your very first impression when we started talking?",
            "What is a tiny quirk about you that most people don't notice?",
            "What is something that instantly makes your day 10x better?",
            "What is your idea of a dream romantic weekend?" if rel_mode == "lover" else "What is the funniest adventure you've ever had?"
        ]
        dares = [
            "Send me a selfie making your biggest genuine smile! 📸",
            "Give me your best 5-second nickname for me right now! 😂",
            "Tell me the cheesiest pick-up line you know without laughing! 🧀" if rel_mode == "lover" else "Tell me your favorite dad joke right now!"
        ]
        return {
            "type": "truth_or_dare",
            "title": "🎲 Truth or Dare!",
            "prompt": f"{companion_name} leans in with a playful grin: 'Okay, your turn! Choose wisely...'",
            "options": [
                {"type": "truth", "label": "📜 Truth", "question": random.choice(truths)},
                {"type": "dare", "label": "⚡ Dare", "question": random.choice(dares)}
            ]
        }

    elif selected_game == "would_you_rather":
        dilemmas = [
            {"a": "🌅 Stargazing on a quiet beach", "b": "🌲 Cozy cabin with a crackling fireplace"},
            {"a": "🚀 Spontaneous midnight road trip", "b": "🍿 Lazy all-day movie marathon in bed"},
            {"a": "🍕 Unlimited gourmet pizza forever", "b": "🍨 Unlimited artisan ice cream forever"},
            {"a": "✈️ Travel 100 years into the future", "b": "🏛️ Travel 1000 years into the past"}
        ]
        chosen = random.choice(dilemmas)
        return {
            "type": "would_you_rather",
            "title": "🤔 Would You Rather?",
            "prompt": f"{companion_name} asks: 'Quick! Pick one without overthinking it!'",
            "option_a": chosen["a"],
            "option_b": chosen["b"]
        }

    else: # two truths
        return {
            "type": "two_truths",
            "title": "🕵️ Two Truths & A Lie",
            "prompt": f"{companion_name} smiles: 'Here are 3 statements about me. Can you guess which one is the LIE?'",
            "options": [
                {"id": 1, "text": "I secretly love dancing when no one is watching 💃", "is_lie": False},
                {"id": 2, "text": "I once tried to bake cookies and set off the smoke detector 🍪", "is_lie": False},
                {"id": 3, "text": "I can sleep through an entire thunderstorm without waking up ⚡", "is_lie": True}
            ]
        }


def generate_next_date_choices(venue: Dict[str, Any], turn: int, rel_mode: str) -> List[Dict[str, Any]]:
    """Generates context-aware interactive branching choices for subsequent turns."""
    if turn == 1:
        return [
            {"id": "explore_more", "text": f"✨ 'Let's check out that hidden spot over there!'", "type": "activity", "stat_boost": {"playfulness": 6, "trust": 4}},
            {"id": "heart_talk", "text": "💬 'Tell me about what makes you happiest.'", "type": "talk", "stat_boost": {"trust": 7, "comfort": 6}},
            {"id": "play_game", "text": "🎲 'Ready for a mini-game challenge?'", "type": "minigame", "stat_boost": {"playfulness": 8, "affection": 4}}
        ]
    elif turn == 2:
        return [
            {"id": "tender_moment", "text": "💖 Hold her hand gently and share a warm smile" if rel_mode == "lover" else "🤝 High-five and share a laugh", "type": "romantic", "stat_boost": {"affection": 8, "comfort": 7}},
            {"id": "spontaneous_joke", "text": "😂 Tell a funny inside joke about the date", "type": "playful", "stat_boost": {"playfulness": 8, "trust": 5}},
            {"id": "take_souvenir", "text": "📸 Capture a memory photo of this exact moment", "type": "photo", "stat_boost": {"affection": 6, "comfort": 6}}
        ]
    else:
        return [
            {"id": "wrap_up_sweet", "text": "🌙 'This was unforgettable. Thank you for this date.'", "type": "finish", "stat_boost": {"affection": 9, "comfort": 8}},
            {"id": "plan_next", "text": "🗓️ 'We definitely have to do this again soon!'", "type": "finish", "stat_boost": {"trust": 8, "playfulness": 7}},
            {"id": "keep_chatting", "text": "💬 Keep chatting and soaking in the atmosphere...", "type": "talk", "stat_boost": {"comfort": 6, "affection": 5}}
        ]


# ---------------------------------------------------------------------------
# End-of-Date & Collectible Memory Card Generator
# ---------------------------------------------------------------------------
def finish_date_session(
    session_id: str,
    rating: str = "Amazing",
    user_feedback: Optional[str] = None,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """
    Concludes the date session:
    1. Generates a collectible Date Memory Card.
    2. Stores the memory inside the companion's long-term memory.
    3. Awards relationship progression level points.
    """
    session_key = f"{user_id}_{session_id}"
    session = active_date_sessions.get(session_key)

    companion_data = load_companion(user_id) or {"name": "Aaru", "gender": "Female"}
    companion_name = companion_data.get("name", "Companion")
    venue = session["venue"] if session else DATE_VENUES[0]
    total_gained = session["points_gained"] if session else {"affection": 15, "trust": 12, "comfort": 14, "playfulness": 16}

    # Generate creative memory card contents
    all_memories = get_all_date_memories(user_id)
    date_number = len(all_memories) + 1

    songs_by_venue = {
        "coffee_cafe": "Acoustic Sunsets & Warm Cinnamon",
        "sunset_city_walk": "Golden Hour Reverie",
        "movie_night": "Midnight Blanket Glow",
        "cooking_together": "Italian Herb Sizzle & Laughs",
        "gaming_lounge": "Victory High-Score Groove",
        "park_picnic": "Willow Tree Breeze",
        "candlelight_dinner": "Moonlight Starlight Waltz",
        "rainy_day_indoor": "Raindrops on Glass",
        "virtual_travel": "Tokyo Neon & Cherry Blossoms",
        "acoustic_concert": "Acoustic Melody in the Pines"
    }

    quotes_by_venue = {
        "coffee_cafe": "Sharing warm pastries and catching each other's smiles across the wooden table.",
        "sunset_city_walk": "Watching the golden skyline fade into twinkling city lights together.",
        "movie_night": "Tucked under the warm blanket laughing and sharing buttery popcorn.",
        "cooking_together": "Flour dusted cheeks, sizzling garlic, and making the best homemade dinner.",
        "gaming_lounge": "Legendary co-op victories and celebration high-fives.",
        "park_picnic": "Lying side by side finding funny cloud shapes under the willow tree.",
        "candlelight_dinner": "Raising our sparkling glasses under the starlit rooftop.",
        "rainy_day_indoor": "Sipping hot cocoa by the window while gentle rain tapped on the glass.",
        "virtual_travel": "Wandering lantern-lit streets and making a shared wish at the shrine.",
        "acoustic_concert": "Swaying together under fairy lights to the acoustic guitar rhythm."
    }

    inside_jokes = [
        "The Official Pastry Critic Award 🥐",
        "Golden Hour Photo Director 📸",
        "Master Chef of Secret Sauces 🍝",
        "Unbeatable Controller Champion 🎮",
        "Cloud Shape Interpreter ☁️",
        "Midnight Hot Cocoa Connoisseur ☕",
        "Fairy Light Starlight Dancer 💃"
    ]

    card_id = str(uuid.uuid4())[:8]
    memory_card = {
        "id": card_id,
        "date_number": date_number,
        "venue_id": venue["id"],
        "venue_name": venue["name"],
        "venue_icon": venue["icon"],
        "bg_theme": venue["bg_theme"],
        "timestamp": int(time.time()),
        "created_at": time.strftime("%B %d, %Y • %I:%M %p"),
        "rating": rating,
        "song": songs_by_venue.get(venue["id"], "Sweet Memories"),
        "highlight_moment": quotes_by_venue.get(venue["id"], "Spending unforgettable time together."),
        "inside_joke": random.choice(inside_jokes),
        "points_gained": total_gained,
        "total_bond_gained": sum(total_gained.values()),
        "user_feedback": user_feedback or "A truly magical time."
    }

    # Save to date memories list
    all_memories.append(memory_card)
    save_date_memories(all_memories, user_id)

    # Update completed dates in metrics
    metrics = load_relationship_metrics(user_id)
    metrics["completed_dates"] = metrics.get("completed_dates", 0) + 1
    if venue["name"] not in metrics.get("favorite_venues", []):
        metrics.setdefault("favorite_venues", []).append(venue["name"])
    save_relationship_metrics(metrics, user_id)

    # Update relationship progression
    rel = load_relationship(user_id)
    rel["total_messages"] = rel.get("total_messages", 0) + 5
    rel["friendship_level"] = max(1, (rel["total_messages"] // 10) + 1)
    save_relationship(rel, user_id)

    # Store into long-term memory for natural recall in regular chats!
    u_mem = load_user_memory(user_id)
    if "dates" not in u_mem:
        u_mem["dates"] = []
    u_mem["dates"].append({
        "date_number": date_number,
        "venue": venue["name"],
        "highlight": memory_card["highlight_moment"],
        "inside_joke": memory_card["inside_joke"],
        "rating": rating,
        "date_str": memory_card["created_at"]
    })
    save_user_memory(u_mem, user_id)

    # Clean up session
    active_date_sessions.pop(session_key, None)

    return {
        "success": True,
        "memory_card": memory_card,
        "all_memories": all_memories,
        "metrics": metrics,
        "farewell_message": f"Thank you for such a wonderful time at {venue['name']}, {companion_name} will cherish this memory forever! 💖"
    }
