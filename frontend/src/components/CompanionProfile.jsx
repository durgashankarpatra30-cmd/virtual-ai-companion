import { useState, useEffect } from "react";
import api, { getFullAssetUrl } from "../services/api";
import { companionAudioManager } from "../services/audioService";
import { getUserId, resetUserSession } from "../services/userSession";
import "../style/CompanionProfile.css";

const INPUT_LANGUAGES = [
    { code: "en-US", label: "English (US)" },
    { code: "en-GB", label: "English (UK)" },
    { code: "en-IN", label: "English (India)" },
    { code: "es-ES", label: "Spanish (Español)" },
    { code: "fr-FR", label: "French (Français)" },
    { code: "de-DE", label: "German (Deutsch)" },
    { code: "hi-IN", label: "Hindi (हिंदी)" },
    { code: "ja-JP", label: "Japanese (日本語)" },
];

const RELATIONSHIP_MODE_OPTIONS = [
    { id: "friendship", label: "🤝 Friendship (Best Buddy)", desc: "Informal, cheerful, boundary in intimacy" },
    { id: "mentor", label: "🎓 Mentor (Coach & Guide)", desc: "Strictly official, professional, growth-focused" },
    { id: "lover", label: "❤️ Lover (Romantic Partner)", desc: "Affectionate, intimate, devoted, sweet & clingy" },
];

function CompanionProfile({
    companion,
    avatarUrl,
    onClose,
    onOpenPhotoStudio,
    onOpenDateModal,
    onOpenNewCharacter,
    onCompanionUpdated
}) {
    const [recentPhotos, setRecentPhotos] = useState([]);
    const [availableVoices, setAvailableVoices] = useState([]);
    const [selectedVoice, setSelectedVoice] = useState(companion?.voice_id || "en-US-AriaNeural");
    const [selectedSpeed, setSelectedSpeed] = useState(companion?.voice_speed || "+0%");
    const [selectedMode, setSelectedMode] = useState(companion?.relationship_mode || companion?.relationship?.relationship_mode || "friendship");
    const [autoPlayVoice, setAutoPlayVoice] = useState(companionAudioManager.getAutoPlay());
    const [inputLanguage, setInputLanguage] = useState(localStorage.getItem("virtual_companion_input_lang") || "en-US");
    const [isTestingVoice, setIsTestingVoice] = useState(false);
    const [isSavingVoice, setIsSavingVoice] = useState(false);
    const [saveStatus, setSaveStatus] = useState("");
    const [userIdState, setUserIdState] = useState(getUserId());
    const [copiedSession, setCopiedSession] = useState(false);

    useEffect(() => {
        const fetchRecentPhotos = async () => {
            try {
                const res = await api.get("/image-history");
                setRecentPhotos((res.data.history || []).slice(0, 4));
            } catch (e) {
                console.error("Failed to load recent photos:", e);
            }
        };

        const fetchVoices = async () => {
            try {
                const res = await api.get("/voices");
                if (res.data && res.data.voices) {
                    setAvailableVoices(res.data.voices);
                }
            } catch (e) {
                console.error("Failed to load voices:", e);
            }
        };

        fetchRecentPhotos();
        fetchVoices();
    }, []);

    const getAvatarSrc = () => {
        const url = avatarUrl || companion?.avatar_url || companion?.avatar?.url;
        if (!url) return null;
        return getFullAssetUrl(url);
    };

    const avatarSrc = getAvatarSrc();
    const genderIcon = companion?.gender === "Male" ? "♂ Male" : companion?.gender === "Non-Binary" ? "⚧ Non-Binary" : "♀ Female";
    const currentMode = companion?.relationship_mode || companion?.relationship?.relationship_mode || "friendship";
    const modeBadge = currentMode === "mentor" ? "🎓 Mentor" : currentMode === "lover" ? "❤️ Lover" : "🤝 Friend";

    // Test Voice preview sample
    const handleTestVoice = async (voiceId) => {
        const targetVoice = voiceId || selectedVoice;
        setIsTestingVoice(true);
        try {
            const sampleText = `Hello! I'm ${companion?.name || "your companion"}. It's so lovely to speak with you!`;
            const res = await api.post("/tts", {
                text: sampleText,
                voice_id: targetVoice,
                rate: selectedSpeed
            });

            if (res.data && res.data.audio && res.data.audio.url) {
                companionAudioManager.play(res.data.audio.url, "preview-track");
            } else {
                companionAudioManager.speakTextFallback(sampleText, companion?.gender);
            }
        } catch (err) {
            console.warn("Voice preview error:", err);
            companionAudioManager.speakTextFallback("Hello! How are you doing today?", companion?.gender);
        } finally {
            setIsTestingVoice(false);
        }
    };

    // Save Voice & Mode Settings
    const handleSaveSettings = async () => {
        setIsSavingVoice(true);
        setSaveStatus("");
        try {
            const res = await api.post("/companion/voice", {
                voice_id: selectedVoice,
                voice_speed: selectedSpeed,
                relationship_mode: selectedMode,
            });

            companionAudioManager.setAutoPlay(autoPlayVoice);
            localStorage.setItem("virtual_companion_input_lang", inputLanguage);

            if (res.data && res.data.companion) {
                if (onCompanionUpdated) {
                    onCompanionUpdated(res.data.companion);
                }
            }
            setSaveStatus("✅ Settings saved successfully!");
            setTimeout(() => setSaveStatus(""), 3000);
        } catch (e) {
            console.error("Failed to save settings:", e);
            setSaveStatus("❌ Error saving settings");
        } finally {
            setIsSavingVoice(false);
        }
    };

    const handleCopySession = () => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(userIdState);
            setCopiedSession(true);
            setTimeout(() => setCopiedSession(false), 2500);
        }
    };

    const handleResetSession = () => {
        if (window.confirm("Start a brand new profile on this device? Your current character & chats will be safely detached.")) {
            resetUserSession();
            window.location.reload();
        }
    };

    return (
        <div className="profile-overlay">
            <div className="profile-card">
                <button className="close-btn" onClick={onClose} title="Close">
                    ✕
                </button>

                <div className="profile-avatar-container">
                    <div className="profile-avatar">
                        {avatarSrc ? (
                            <img src={avatarSrc} alt={companion?.name || "Avatar"} className="profile-avatar-img" />
                        ) : (
                            <span>{companion?.gender === "Male" ? "👨" : "👩"}</span>
                        )}
                    </div>
                </div>

                <h2>{companion?.name}</h2>

                <p className="profile-status">
                    🟢 {companion?.status || "Online"} • {genderIcon} • <span className="profile-mode-badge">{modeBadge}</span>
                </p>

                {/* Profile Actions */}
                <div className="profile-action-row">
                    <button
                        className="profile-date-night-btn"
                        onClick={() => {
                            onClose();
                            if (onOpenDateModal) onOpenDateModal();
                        }}
                    >
                        🌹 {relMode === "lover" ? "Virtual Date" : relMode === "mentor" ? "Strategy Session" : "Hangout & Activities"}
                    </button>

                    <button
                        className="profile-photo-studio-btn"
                        onClick={() => {
                            onClose();
                            if (onOpenPhotoStudio) onOpenPhotoStudio();
                        }}
                    >
                        📸 Photo Studio
                    </button>

                    <button
                        className="profile-switch-character-btn"
                        onClick={() => {
                            onClose();
                            if (onOpenNewCharacter) onOpenNewCharacter();
                        }}
                    >
                        🔄 Switch / New
                    </button>
                </div>

                <hr/>

                <div className="profile-grid">
                    <div>
                        <strong>🎂 Age & Gender</strong>
                        <p>{companion?.age} yrs • {companion?.gender || "Female"}</p>
                    </div>

                    <div>
                        <strong>🌟 Bond Level</strong>
                        <p>Level {companion?.relationship?.friendship_level ?? companion?.friendship_level ?? 1}</p>
                    </div>

                    <div>
                        <strong>💬 Messages</strong>
                        <p>{companion?.relationship?.total_messages ?? companion?.total_messages ?? 0}</p>
                    </div>

                    <div>
                        <strong>🎭 Relationship Stage</strong>
                        <p>{companion?.relationship?.relationship_stage || "New Companion"}</p>
                    </div>
                </div>

                <hr/>

                {/* Relationship Mode Selector */}
                <div className="section mode-settings-section">
                    <h3>🎭 Relationship Mode</h3>
                    <p className="section-desc">Change how {companion?.name || "your companion"} behaves and defines intimacy boundaries:</p>

                    <div className="mode-options-list">
                        {RELATIONSHIP_MODE_OPTIONS.map((m) => (
                            <label
                                key={m.id}
                                className={`mode-option-card ${selectedMode === m.id ? "selected" : ""}`}
                            >
                                <input
                                    type="radio"
                                    name="relMode"
                                    value={m.id}
                                    checked={selectedMode === m.id}
                                    onChange={() => setSelectedMode(m.id)}
                                />
                                <div className="mode-option-text">
                                    <strong>{m.label}</strong>
                                    <p>{m.desc}</p>
                                </div>
                            </label>
                        ))}
                    </div>
                </div>

                <hr/>

                {/* Voice & Audio Customization Section */}
                <div className="section voice-settings-section">
                    <h3>🎙️ Voice & Audio Settings</h3>

                    {/* Auto-play toggle */}
                    <div className="voice-toggle-row">
                        <div className="voice-toggle-label">
                            <strong>🔊 Auto-Play Companion Voice</strong>
                            <p>Automatically read new responses aloud</p>
                        </div>
                        <label className="switch">
                            <input
                                type="checkbox"
                                checked={autoPlayVoice}
                                onChange={(e) => {
                                    setAutoPlayVoice(e.target.checked);
                                    companionAudioManager.setAutoPlay(e.target.checked);
                                }}
                            />
                            <span className="slider round"></span>
                        </label>
                    </div>

                    {/* Voice Persona Selector */}
                    <div className="voice-select-field">
                        <label><strong>Companion Voice Persona:</strong></label>
                        <div className="voice-selector-box">
                            <select
                                value={selectedVoice}
                                onChange={(e) => setSelectedVoice(e.target.value)}
                                className="voice-select-dropdown"
                            >
                                {availableVoices.map((v) => (
                                    <option key={v.id} value={v.id}>
                                        {v.name} ({v.gender} • {v.accent})
                                    </option>
                                ))}
                            </select>

                            <button
                                type="button"
                                className="voice-test-btn"
                                onClick={() => handleTestVoice(selectedVoice)}
                                disabled={isTestingVoice}
                                title="Listen to a voice preview sample"
                            >
                                {isTestingVoice ? "⏳" : "▶ Test"}
                            </button>
                        </div>
                    </div>

                    {/* Speech Speed */}
                    <div className="voice-select-field">
                        <label><strong>Speaking Speed:</strong></label>
                        <select
                            value={selectedSpeed}
                            onChange={(e) => setSelectedSpeed(e.target.value)}
                            className="voice-select-dropdown"
                        >
                            <option value="-15%">Slower (0.85x)</option>
                            <option value="+0%">Normal (1.0x)</option>
                            <option value="+15%">Lively (1.15x)</option>
                            <option value="+30%">Fast (1.3x)</option>
                        </select>
                    </div>

                    {/* Voice Input Language */}
                    <div className="voice-select-field">
                        <label><strong>Speech Recognition Language (Mic):</strong></label>
                        <select
                            value={inputLanguage}
                            onChange={(e) => setInputLanguage(e.target.value)}
                            className="voice-select-dropdown"
                        >
                            {INPUT_LANGUAGES.map((lang) => (
                                <option key={lang.code} value={lang.code}>
                                    {lang.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        type="button"
                        className="save-voice-btn"
                        onClick={handleSaveSettings}
                        disabled={isSavingVoice}
                    >
                        {isSavingVoice ? "Saving..." : "💾 Save Companion Settings"}
                    </button>

                    {saveStatus && <p className="save-status-msg">{saveStatus}</p>}
                </div>

                <hr/>

                {/* Device & Privacy Session Info */}
                <div className="section privacy-session-section">
                    <h3>🔒 Device Privacy & Data Isolation</h3>
                    <p className="privacy-desc">Your chat messages, memories, and character are strictly isolated to your device and never shared with other users.</p>
                    <div className="session-id-row">
                        <span className="session-label">Profile Key:</span>
                        <code className="session-code">{userIdState.substring(0, 16)}...</code>
                        <button className="copy-session-btn" onClick={handleCopySession}>
                            {copiedSession ? "✓ Copied" : "📋 Copy"}
                        </button>
                    </div>
                    <button className="reset-session-btn" onClick={handleResetSession}>
                        🔄 Reset Device Profile (Start Fresh)
                    </button>
                </div>

                <hr/>

                {/* Recent Photos Mini-Gallery */}
                {recentPhotos.length > 0 && (
                    <div className="section">
                        <div className="recent-photos-header">
                            <h3>📷 Recent Photos</h3>
                            <button
                                className="view-all-photos-btn"
                                onClick={() => {
                                    onClose();
                                    if (onOpenPhotoStudio) onOpenPhotoStudio();
                                }}
                            >
                                View All →
                            </button>
                        </div>
                        <div className="recent-photos-grid">
                            {recentPhotos.map((photo) => (
                                <div key={photo.id} className="recent-photo-item" title={photo.scene}>
                                    <img
                                        src={getFullAssetUrl(photo.url)}
                                        alt={photo.scene || "Photo"}
                                    />
                                    <span className="recent-photo-tag">{photo.scene || "Portrait"}</span>
                                </div>
                            ))}
                        </div>
                        <hr/>
                    </div>
                )}

                <div className="section">
                    <h3>🌟 Traits</h3>
                    <p>{Array.isArray(companion?.traits) ? companion?.traits?.join(", ") : companion?.traits}</p>
                </div>

                <div className="section">
                    <h3>🎵 Hobbies</h3>
                    <p>{Array.isArray(companion?.hobbies) ? companion?.hobbies?.join(", ") : companion?.hobbies}</p>
                </div>

                <div className="section">
                    <h3>🎯 Goal</h3>
                    <p>{companion?.goal}</p>
                </div>

                <div className="section">
                    <h3>🗣️ Speaking Style</h3>
                    <p>{companion?.speaking_style || "Friendly"}</p>
                </div>
            </div>
        </div>
    );
}

export default CompanionProfile;