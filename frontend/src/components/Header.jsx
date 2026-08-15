import { useState, useEffect } from "react";
import { companionAudioManager } from "../services/audioService";
import { getFullAssetUrl } from "../services/api";
import "../style/Header.css";

function Header({
    companion,
    avatarUrl,
    voiceMode,
    onToggleVoiceMode,
    onProfileClick,
    onPhotoStudioClick,
    onNewCharacterClick,
    onOpenVipModal
}) {
    const [isSpeaking, setIsSpeaking] = useState(false);

    useEffect(() => {
        const unsubscribe = companionAudioManager.subscribe((state) => {
            if (typeof state.isSpeaking === "boolean") {
                setIsSpeaking(state.isSpeaking);
            }
        });
        return unsubscribe;
    }, []);

    const getAvatarSrc = () => {
        const url = avatarUrl || companion?.avatar_url || companion?.avatar?.url;
        if (!url) return null;
        return getFullAssetUrl(url);
    };

    const avatarSrc = getAvatarSrc();
    const genderIcon = companion?.gender === "Male" ? "♂" : companion?.gender === "Non-Binary" ? "⚧" : "♀";

    return (
        <header className="header">
            <div className="header-left">
                <div
                    className={`avatar ${isSpeaking ? "avatar-speaking" : ""}`}
                    onClick={onProfileClick}
                    title="View Profile"
                >
                    {avatarSrc ? (
                        <img src={avatarSrc} alt={companion?.name || "Avatar"} className="avatar-img" />
                    ) : (
                        <span>{companion?.gender === "Male" ? "👨" : "👩"}</span>
                    )}

                    {/* Speaking animated indicator waves */}
                    {isSpeaking && (
                        <div className="avatar-speaking-waves">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    )}
                </div>

                <div className="companion-info">
                    <h1 className="companion-name" onClick={onProfileClick}>
                        {companion?.name || "Companion"} <span className="header-gender-badge">{genderIcon}</span>
                    </h1>

                    <div className="status">
                        <span className="online-dot"></span>
                        <span>{isSpeaking ? "🗣️ Speaking..." : "🟢 Online"}</span>
                    </div>
                </div>
            </div>

            <div className="header-right">
                {/* VIP Upgrade Button */}
                <button
                    className="vip-header-btn"
                    onClick={onOpenVipModal}
                    title="Upgrade to VIP / Pro Membership"
                >
                    💎 VIP
                </button>

                {/* Voice Mode Toggle Button */}
                <button
                    className={`voice-mode-btn ${voiceMode ? "voice-mode-active" : "voice-mode-muted"}`}
                    onClick={onToggleVoiceMode}
                    title={voiceMode ? "Voice Output is ON (Auto-plays responses). Click to Mute." : "Voice Output is MUTED. Click to Enable."}
                >
                    {voiceMode ? "🔊 Voice: ON" : "🔇 Voice: OFF"}
                </button>

                {/* Switch / New Character Button */}
                <button
                    className="new-character-btn"
                    onClick={onNewCharacterClick}
                    title="Create or switch companion"
                >
                    🔄 Characters
                </button>

                {/* Photo Studio Button */}
                <button
                    className="photo-studio-btn"
                    onClick={onPhotoStudioClick}
                    title="Generate photos and selfies"
                >
                    📸 Photos
                </button>

                <div className="info-card">
                    <span>😊 {companion?.relationship?.current_mood || companion?.mood || "Neutral"}</span>
                </div>

                <div className="info-card">
                    <span>❤️ Lv {companion?.relationship?.friendship_level ?? companion?.friendship_level ?? 0}</span>
                </div>

                <div className="info-card">
                    <span>💬 {companion?.relationship?.total_messages ?? companion?.total_messages ?? 0}</span>
                </div>

                <button
                    className="settings-btn"
                    onClick={onProfileClick}
                    title="Profile & Settings"
                >
                    ⚙
                </button>
            </div>
        </header>
    );
}

export default Header;