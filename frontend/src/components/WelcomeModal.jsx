import { useState } from "react";
import api, { getFullAssetUrl } from "../services/api";
import "../style/WelcomeModal.css";

const PRESET_TRAITS = [
    "Kind", "Sweet", "Caring", "Witty", "Playful", "Loyal",
    "Sassy", "Adventurous", "Creative", "Intelligent", "Empathetic", "Humorous"
];

const PRESET_HOBBIES = [
    "Singing", "Dancing", "Reading", "Gaming", "Cooking", "Photography",
    "Coding", "Painting", "Traveling", "Fitness", "Anime", "Music"
];

const SPEAKING_STYLES = [
    { id: "Sweet", label: "Sweet & Caring 💖", desc: "Warm, supportive, and affectionate" },
    { id: "Cheerful", label: "Cheerful & Energetic ⚡", desc: "High energy, enthusiastic, and bright" },
    { id: "Calm", label: "Calm & Gentle 🌿", desc: "Relaxed, soothing, and thoughtful" },
    { id: "Witty", label: "Witty & Sarcastic 😏", desc: "Playful teasing, clever banter, and humorous" },
    { id: "Poetic", label: "Poetic & Deep 🌌", desc: "Philosophical, dreamy, and emotional" },
    { id: "Intelligent", label: "Smart & Intellectual 🎓", desc: "Logical, knowledgeable, and curious" }
];

const HAIR_STYLES = {
    Female: [
        { label: "Long Straight Black", color: "Black", style: "Long Straight" },
        { label: "Wavy Dark Brown", color: "Dark Brown", style: "Wavy Shoulder-Length" },
        { label: "Soft Auburn Curls", color: "Auburn", style: "Curly Medium" },
        { label: "Blonde Bob Cut", color: "Honey Blonde", style: "Sleek Bob" },
        { label: "Silver Highlights", color: "Dark with Silver Highlights", style: "Layered" }
    ],
    Male: [
        { label: "Short Textured Dark", color: "Dark Brown", style: "Short Textured Crop" },
        { label: "Messy Undercut Black", color: "Black", style: "Undercut with Volume" },
        { label: "Side-Part Classic", color: "Black", style: "Classic Side-Part" },
        { label: "Wavy Medium Brown", color: "Brown", style: "Medium Wavy" },
        { label: "Clean Fade & Comb", color: "Dark Charcoal", style: "Modern Fade" }
    ],
    "Non-Binary": [
        { label: "Short Layered Shag", color: "Dark Brown", style: "Textured Shag" },
        { label: "Androgynous Wolf Cut", color: "Black", style: "Modern Wolf Cut" },
        { label: "Sleek Pixie Cut", color: "Silver Grey", style: "Pixie Cut" },
        { label: "Wavy Shoulder-Length", color: "Chestnut", style: "Natural Waves" }
    ]
};

const SKIN_TONES = ["Fair", "Warm Beige", "Sun-Kissed Tan", "Deep Olive", "Rich Warm Brown"];
const EYE_COLORS = ["Deep Brown", "Hazel", "Emerald Green", "Sapphire Blue", "Warm Amber"];
const OUTFIT_STYLES = [
    "Cozy Oversized Hoodie & Jeans",
    "Chic Smart Casual Blazer & Tee",
    "Modern Streetwear Jacket",
    "Classic Denim & White Sneakers",
    "Elegant Knit Sweater"
];

const VOICE_OPTIONS_BY_GENDER = {
    Female: [
        { id: "en-US-AriaNeural", name: "Aria", desc: "Warm & Expressive (US)" },
        { id: "en-US-AnaNeural", name: "Ana", desc: "Sweet & Gentle (US)" },
        { id: "en-US-JennyNeural", name: "Jenny", desc: "Cheerful & Lively (US)" },
        { id: "en-GB-SoniaNeural", name: "Sonia", desc: "Elegant & Calm (UK)" },
    ],
    Male: [
        { id: "en-US-GuyNeural", name: "Guy", desc: "Warm & Friendly (US)" },
        { id: "en-US-ChristopherNeural", name: "Christopher", desc: "Deep & Calm (US)" },
        { id: "en-US-EricNeural", name: "Eric", desc: "Upbeat & Playful (US)" },
        { id: "en-GB-RyanNeural", name: "Ryan", desc: "Gentle British (UK)" },
    ],
    "Non-Binary": [
        { id: "en-US-AriaNeural", name: "Aria", desc: "Warm & Expressive (US)" },
        { id: "en-US-GuyNeural", name: "Guy", desc: "Warm & Friendly (US)" },
        { id: "en-US-AnaNeural", name: "Ana", desc: "Sweet & Gentle (US)" },
        { id: "en-GB-SoniaNeural", name: "Sonia", desc: "Elegant British (UK)" },
    ]
};

function WelcomeModal({
    existingCompanion,
    avatarUrl,
    onContinueExisting,
    onCompanionCreated,
    canClose = false,
    onClose
}) {
    // Mode: 'select' (choose existing vs new) or 'create' (create form)
    const [mode, setMode] = useState(existingCompanion && existingCompanion.name ? "select" : "create");

    // Form State
    const [name, setName] = useState("");
    const [gender, setGender] = useState("Female");
    const [age, setAge] = useState(20);
    const [speakingStyle, setSpeakingStyle] = useState("Sweet");
    const [voiceId, setVoiceId] = useState("en-US-AriaNeural");
    const [goal, setGoal] = useState("Becoming a doctor");
    const [selectedTraits, setSelectedTraits] = useState(["Kind", "Sweet", "Caring"]);
    const [customTrait, setCustomTrait] = useState("");
    const [selectedHobbies, setSelectedHobbies] = useState(["Reading", "Dancing", "Music"]);
    const [customHobby, setCustomHobby] = useState("");

    // Visual / Appearance State for AI Image Generation
    const [skinTone, setSkinTone] = useState("Fair");
    const [selectedHairIdx, setSelectedHairIdx] = useState(0);
    const [eyeColor, setEyeColor] = useState("Deep Brown");
    const [clothingStyle, setClothingStyle] = useState(OUTFIT_STYLES[0]);
    const [generateInitialAvatar, setGenerateInitialAvatar] = useState(true);

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [statusMessage, setStatusMessage] = useState("");

    const hairOptions = HAIR_STYLES[gender] || HAIR_STYLES.Female;

    const toggleTrait = (trait) => {
        setSelectedTraits((prev) =>
            prev.includes(trait) ? prev.filter((t) => t !== trait) : [...prev, trait]
        );
    };

    const addCustomTrait = () => {
        if (customTrait.trim() && !selectedTraits.includes(customTrait.trim())) {
            setSelectedTraits((prev) => [...prev, customTrait.trim()]);
            setCustomTrait("");
        }
    };

    const toggleHobby = (hobby) => {
        setSelectedHobbies((prev) =>
            prev.includes(hobby) ? prev.filter((h) => h !== hobby) : [...prev, hobby]
        );
    };

    const addCustomHobby = () => {
        if (customHobby.trim() && !selectedHobbies.includes(customHobby.trim())) {
            setSelectedHobbies((prev) => [...prev, customHobby.trim()]);
            setCustomHobby("");
        }
    };

    const handleCreateSubmit = async (e) => {
        e.preventDefault();
        if (!name.trim()) {
            alert("Please enter a name for your companion!");
            return;
        }

        setIsSubmitting(true);
        setStatusMessage("Creating companion profile & personality...");

        const hairChoice = hairOptions[selectedHairIdx] || hairOptions[0];

        const payload = {
            name: name.trim(),
            gender: gender,
            age: parseInt(age) || 20,
            traits: selectedTraits.length > 0 ? selectedTraits : ["Kind", "Friendly"],
            hobbies: selectedHobbies.length > 0 ? selectedHobbies : ["Reading"],
            speaking_style: speakingStyle,
            goal: goal.trim() || "Be your best friend",
            voice_id: voiceId,
            skin_tone: skinTone,
            hair_color: hairChoice.color,
            hair_style: hairChoice.style,
            eye_color: eyeColor,
            clothing_style: clothingStyle,
            generate_avatar: generateInitialAvatar
        };

        const statusInterval = setInterval(() => {
            const msgs = [
                "Generating companion's photorealistic portrait...",
                "Styling character features & appearance...",
                "Setting up memory & conversational engine...",
                "Almost ready to meet you..."
            ];
            setStatusMessage((prev) => {
                const idx = (msgs.indexOf(prev) + 1) % msgs.length;
                return msgs[idx];
            });
        }, 3000);

        try {
            const response = await api.post("/companion/create", payload);
            clearInterval(statusInterval);

            if (response.data && response.data.success) {
                if (onCompanionCreated) {
                    onCompanionCreated(response.data.companion, response.data.avatar);
                }
            }
        } catch (err) {
            clearInterval(statusInterval);
            console.error("Error creating companion:", err);
            alert("Failed to create companion. Please make sure the backend server is running!");
        } finally {
            setIsSubmitting(false);
            setStatusMessage("");
        }
    };

    const getFullImageUrl = (relativeUrl) => {
        if (!relativeUrl) return null;
        return getFullAssetUrl(relativeUrl);
    };

    const existingAvatarSrc = getFullImageUrl(avatarUrl || existingCompanion?.avatar_url || existingCompanion?.avatar?.url);

    return (
        <div className="welcome-modal-overlay">
            <div className="welcome-modal-card">
                {canClose && (
                    <button className="welcome-close-btn" onClick={onClose}>✕</button>
                )}

                {/* MODE 1: SELECT EXISTING OR CREATE NEW */}
                {mode === "select" && existingCompanion && (
                    <div className="welcome-select-view">
                        <div className="welcome-hero">
                            <span className="welcome-badge">✨ Virtual AI Companion</span>
                            <h1>Welcome Back!</h1>
                            <p>Continue your journey with your companion or bring a brand new character to life.</p>
                        </div>

                        <div className="existing-companion-card">
                            <div className="existing-avatar-wrap">
                                {existingAvatarSrc ? (
                                    <img src={existingAvatarSrc} alt={existingCompanion.name} />
                                ) : (
                                    <div className="fallback-avatar">
                                        {existingCompanion.gender === "Male" ? "👨" : "👩"}
                                    </div>
                                )}
                                <span className="online-indicator"></span>
                            </div>

                            <div className="existing-info">
                                <div className="name-row">
                                    <h2>{existingCompanion.name}</h2>
                                    <span className="gender-tag">
                                        {existingCompanion.gender === "Male" ? "♂ Male" : existingCompanion.gender === "Non-Binary" ? "⚧ Non-Binary" : "♀ Female"} • {existingCompanion.age} yrs
                                    </span>
                                </div>

                                <p className="existing-goal">🎯 Goal: {existingCompanion.goal || "Companion"}</p>

                                <div className="existing-tags">
                                    {Array.isArray(existingCompanion.traits) && existingCompanion.traits.slice(0, 3).map((t) => (
                                        <span key={t} className="tag-chip">{t}</span>
                                    ))}
                                    {Array.isArray(existingCompanion.hobbies) && existingCompanion.hobbies.slice(0, 2).map((h) => (
                                        <span key={h} className="tag-chip hobby">{h}</span>
                                    ))}
                                </div>

                                <div className="existing-stats-row">
                                    <span>❤️ Friendship Lv {existingCompanion.relationship?.friendship_level ?? existingCompanion.friendship_level ?? 1}</span>
                                    <span>💬 {existingCompanion.relationship?.total_messages ?? existingCompanion.total_messages ?? 0} messages</span>
                                    <span>😊 Mood: {existingCompanion.relationship?.current_mood ?? existingCompanion.mood ?? "Happy"}</span>
                                </div>
                            </div>
                        </div>

                        <div className="welcome-action-buttons">
                            <button
                                className="continue-btn"
                                onClick={() => onContinueExisting && onContinueExisting()}
                            >
                                🚀 Continue with {existingCompanion.name}
                            </button>

                            <button
                                className="create-new-btn"
                                onClick={() => setMode("create")}
                            >
                                ✨ Create New Companion
                            </button>
                        </div>
                    </div>
                )}

                {/* MODE 2: CREATE COMPANION FORM */}
                {mode === "create" && (
                    <div className="welcome-create-view">
                        <div className="create-header">
                            {existingCompanion && (
                                <button className="back-btn" onClick={() => setMode("select")}>
                                    ← Back
                                </button>
                            )}
                            <div className="create-title-area">
                                <h2>✨ Design Your Virtual Companion</h2>
                                <p>Customize identity, personality, speaking style, and visual appearance for AI image generation</p>
                            </div>
                        </div>

                        <form onSubmit={handleCreateSubmit} className="create-form">
                            {/* SECTION 1: IDENTITY */}
                            <div className="form-section">
                                <h3 className="section-title">1. Identity & Demographics</h3>

                                <div className="form-row">
                                    <div className="form-group flex-2">
                                        <label>Companion Name *</label>
                                        <input
                                            type="text"
                                            placeholder="e.g. Aaru, Aarav, Maya, Leo..."
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            required
                                        />
                                    </div>

                                    <div className="form-group flex-1">
                                        <label>Age</label>
                                        <input
                                            type="number"
                                            min="18"
                                            max="60"
                                            value={age}
                                            onChange={(e) => setAge(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Gender (Powers AI Image Generation) *</label>
                                    <div className="gender-selector">
                                        {[
                                            { id: "Female", label: "👩 Female", desc: "Feminine portrait & styling" },
                                            { id: "Male", label: "👨 Male", desc: "Masculine portrait & styling" },
                                            { id: "Non-Binary", label: "🧑 Non-Binary", desc: "Androgynous portrait & styling" }
                                        ].map((g) => (
                                            <div
                                                key={g.id}
                                                className={`gender-card ${gender === g.id ? "selected" : ""}`}
                                                onClick={() => {
                                                    setGender(g.id);
                                                    setSelectedHairIdx(0);
                                                    setVoiceId(g.id === "Male" ? "en-US-GuyNeural" : "en-US-AriaNeural");
                                                }}
                                            >
                                                <span className="gender-title">{g.label}</span>
                                                <span className="gender-desc">{g.desc}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* SECTION 2: PERSONALITY, VOICE & STYLE */}
                            <div className="form-section">
                                <h3 className="section-title">2. Personality & Voice Persona</h3>

                                {/* Voice Persona Selection */}
                                <div className="form-group">
                                    <label>🎙️ Companion Neural Voice Persona</label>
                                    <div className="voice-cards-grid">
                                        {(VOICE_OPTIONS_BY_GENDER[gender] || VOICE_OPTIONS_BY_GENDER.Female).map((v) => (
                                            <div
                                                key={v.id}
                                                className={`voice-card ${voiceId === v.id ? "selected" : ""}`}
                                                onClick={() => setVoiceId(v.id)}
                                            >
                                                <div className="voice-card-header">
                                                    <span className="voice-card-name">🗣️ {v.name}</span>
                                                    {voiceId === v.id && <span className="voice-card-check">✓</span>}
                                                </div>
                                                <p className="voice-card-desc">{v.desc}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Speaking Style & Tone</label>
                                    <div className="speaking-styles-grid">
                                        {SPEAKING_STYLES.map((st) => (
                                            <div
                                                key={st.id}
                                                className={`speaking-card ${speakingStyle === st.id ? "selected" : ""}`}
                                                onClick={() => setSpeakingStyle(st.id)}
                                            >
                                                <strong>{st.label}</strong>
                                                <p>{st.desc}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Personal Dream / Goal</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. Becoming a surgeon, traveling to Japan, releasing an album..."
                                        value={goal}
                                        onChange={(e) => setGoal(e.target.value)}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Personality Traits (Select or Add)</label>
                                    <div className="chips-container">
                                        {PRESET_TRAITS.map((trait) => (
                                            <button
                                                key={trait}
                                                type="button"
                                                className={`chip ${selectedTraits.includes(trait) ? "active" : ""}`}
                                                onClick={() => toggleTrait(trait)}
                                            >
                                                {selectedTraits.includes(trait) ? "✓ " : "+ "}{trait}
                                            </button>
                                        ))}
                                    </div>
                                    <div className="custom-add-row">
                                        <input
                                            type="text"
                                            placeholder="Add custom trait..."
                                            value={customTrait}
                                            onChange={(e) => setCustomTrait(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") {
                                                    e.preventDefault();
                                                    addCustomTrait();
                                                }
                                            }}
                                        />
                                        <button type="button" onClick={addCustomTrait}>Add</button>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Hobbies & Passions</label>
                                    <div className="chips-container">
                                        {PRESET_HOBBIES.map((hobby) => (
                                            <button
                                                key={hobby}
                                                type="button"
                                                className={`chip hobby ${selectedHobbies.includes(hobby) ? "active" : ""}`}
                                                onClick={() => toggleHobby(hobby)}
                                            >
                                                {selectedHobbies.includes(hobby) ? "✓ " : "+ "}{hobby}
                                            </button>
                                        ))}
                                    </div>
                                    <div className="custom-add-row">
                                        <input
                                            type="text"
                                            placeholder="Add custom hobby..."
                                            value={customHobby}
                                            onChange={(e) => setCustomHobby(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") {
                                                    e.preventDefault();
                                                    addCustomHobby();
                                                }
                                            }}
                                        />
                                        <button type="button" onClick={addCustomHobby}>Add</button>
                                    </div>
                                </div>
                            </div>

                            {/* SECTION 3: VISUAL APPEARANCE (IMAGE GENERATION) */}
                            <div className="form-section">
                                <h3 className="section-title">3. Visual Appearance (Powers Photorealistic Image Generator)</h3>

                                <div className="form-row">
                                    <div className="form-group flex-1">
                                        <label>Skin Tone</label>
                                        <select value={skinTone} onChange={(e) => setSkinTone(e.target.value)}>
                                            {SKIN_TONES.map((st) => (
                                                <option key={st} value={st}>{st}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group flex-1">
                                        <label>Eye Color</label>
                                        <select value={eyeColor} onChange={(e) => setEyeColor(e.target.value)}>
                                            {EYE_COLORS.map((ec) => (
                                                <option key={ec} value={ec}>{ec}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Hairstyle & Hair Color</label>
                                    <div className="hair-options-grid">
                                        {hairOptions.map((h, idx) => (
                                            <div
                                                key={h.label}
                                                className={`hair-card ${selectedHairIdx === idx ? "selected" : ""}`}
                                                onClick={() => setSelectedHairIdx(idx)}
                                            >
                                                <span>{h.label}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Default Outfit Style</label>
                                    <select value={clothingStyle} onChange={(e) => setClothingStyle(e.target.value)}>
                                        {OUTFIT_STYLES.map((os) => (
                                            <option key={os} value={os}>{os}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="avatar-gen-checkbox">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={generateInitialAvatar}
                                            onChange={(e) => setGenerateInitialAvatar(e.target.checked)}
                                        />
                                        <span>Automatically generate high-resolution AI portrait avatar on creation</span>
                                    </label>
                                </div>
                            </div>

                            {/* SUBMIT BUTTON */}
                            <div className="form-footer">
                                <button
                                    type="submit"
                                    className="submit-create-btn"
                                    disabled={isSubmitting}
                                >
                                    {isSubmitting ? (
                                        <span className="submitting-state">
                                            <span className="spinner"></span>
                                            {statusMessage || "Bringing your companion to life..."}
                                        </span>
                                    ) : (
                                        `✨ Create ${name || "Companion"} & Start Chatting`
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
}

export default WelcomeModal;
