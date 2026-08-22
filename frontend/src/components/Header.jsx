import { useState, useEffect, useRef } from "react";
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
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const menuRef = useRef(null);

    useEffect(() => {
        const unsubscribe = companionAudioManager.subscribe((state) => {
            if (typeof state.isSpeaking === "boolean") {
                setIsSpeaking(state.isSpeaking);
            }
        });
        return unsubscribe;
    }, []);

    // Close mobile menu on outside click
    useEffect(() => {
        const handleOutsideClick = (e) => {
            if (menuRef.current && !menuRef.current.contains(e.target)) {
                setMobileMenuOpen(false);
            }
        };
        if (mobileMenuOpen) {
            document.addEventListener("mousedown", handleOutsideClick);
            document.addEventListener("touchstart", handleOutsideClick);
        }
        return () => {
            document.removeEventListener("mousedown", handleOutsideClick);
            document.removeEventListener("touchstart", handleOutsideClick);
        };
    }, [mobileMenuOpen]);

    const getAvatarSrc = () => {
        const url = avatarUrl || companion?.avatar_url || companion?.avatar?.url;
        if (!url) return null;
        return getFullAssetUrl(url);
    };

    const avatarSrc = getAvatarSrc();
    const genderIcon = companion?.gender === "Male" ? "♂" : companion?.gender === "Non-Binary" ? "⚧" : "♀";
    const currentMood = companion?.relationship?.current_mood || companion?.mood || "Happy";
    const friendshipLevel = companion?.relationship?.friendship_level ?? companion?.friendship_level ?? 1;
    const totalMessages = companion?.relationship?.total_messages ?? companion?.total_messages ?? 0;
    const stage = companion?.relationship?.relationship_stage || companion?.relationship_stage || "Companion";
    const relMode = companion?.relationship_mode || companion?.relationship?.relationship_mode || "friendship";
    const modeBadge = relMode === "mentor" ? "🎓 Mentor" : relMode === "lover" ? "❤️ Lover" : "🤝 Friend";

    return (
        <header className="header">
            <div className="header-left">
                <div
                    className={`avatar ${isSpeaking ? "avatar-speaking" : ""}`}
                    onClick={onProfileClick}
                    title="View Profile & Settings"
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

                <div className="companion-info" onClick={onProfileClick}>
                    <h1 className="companion-name">
                        <span className="name-text">{companion?.name || "Companion"}</span>
                        <span className="header-gender-badge">{genderIcon}</span>
                        <span className="header-mode-badge">{modeBadge}</span>
                    </h1>

                    <div className="status">
                        <span className="online-dot"></span>
                        <span className="status-text">{isSpeaking ? "Speaking..." : "Online"}</span>
                        <span className="header-stage-pill">{stage}</span>
                    </div>
                </div>
            </div>

            <div className="header-right">
                {/* VIP Upgrade Button */}
                <button
                    className="vip-header-btn"
                    onClick={onOpenVipModal}
                    title="VIP Membership"
                >
                    <span className="btn-icon">💎</span>
                    <span className="btn-label">VIP</span>
                </button>

                {/* Voice Mode Toggle Button */}
                <button
                    className={`voice-mode-btn ${voiceMode ? "voice-mode-active" : "voice-mode-muted"}`}
                    onClick={onToggleVoiceMode}
                    title={voiceMode ? "Voice Output is ON (Auto-plays). Click to Mute." : "Voice Output is MUTED. Click to Enable."}
                >
                    <span className="btn-icon">{voiceMode ? "🔊" : "🔇"}</span>
                    <span className="btn-label">{voiceMode ? "Voice ON" : "Muted"}</span>
                </button>

                {/* Photo Studio Button */}
                <button
                    className="photo-studio-btn"
                    onClick={onPhotoStudioClick}
                    title="Generate photos and selfies"
                >
                    <span className="btn-icon">📸</span>
                    <span className="btn-label">Photos</span>
                </button>

                {/* Desktop-only action items */}
                <button
                    className="new-character-btn desktop-only"
                    onClick={onNewCharacterClick}
                    title="Create or switch companion"
                >
                    <span className="btn-icon">🔄</span>
                    <span className="btn-label">Characters</span>
                </button>

                <div className="info-card desktop-only">
                    <span>{currentMood}</span>
                </div>

                <div className="info-card desktop-only">
                    <span>❤️ Lv {friendshipLevel}</span>
                </div>

                <div className="info-card desktop-only">
                    <span>💬 {totalMessages}</span>
                </div>

                {/* Settings / Menu Toggle Button */}
                <div className="menu-container" ref={menuRef}>
                    <button
                        className={`settings-btn ${mobileMenuOpen ? "active" : ""}`}
                        onClick={() => setMobileMenuOpen((prev) => !prev)}
                        title="Quick Menu & Stats"
                    >
                        ⚙
                    </button>

                    {/* Mobile Quick Dropdown Menu */}
                    {mobileMenuOpen && (
                        <div className="mobile-dropdown-menu">
                            <div className="dropdown-companion-header" onClick={() => { setMobileMenuOpen(false); onProfileClick(); }}>
                                <strong>{companion?.name || "Companion"}</strong>
                                <span className="dropdown-stage-tag">{stage}</span>
                            </div>

                            <div className="dropdown-stats-grid">
                                <div className="stat-pill">
                                    <span className="stat-label">Mood</span>
                                    <span className="stat-val">{currentMood}</span>
                                </div>
                                <div className="stat-pill">
                                    <span className="stat-label">Bond</span>
                                    <span className="stat-val">❤️ Lv {friendshipLevel}</span>
                                </div>
                                <div className="stat-pill">
                                    <span className="stat-label">Messages</span>
                                    <span className="stat-val">💬 {totalMessages}</span>
                                </div>
                            </div>

                            <div className="dropdown-divider"></div>

                            <button
                                className="dropdown-item"
                                onClick={() => { setMobileMenuOpen(false); onProfileClick(); }}
                            >
                                <span>👤</span> Companion Profile & Voice Settings
                            </button>

                            <button
                                className="dropdown-item"
                                onClick={() => { setMobileMenuOpen(false); onNewCharacterClick(); }}
                            >
                                <span>🔄</span> Switch / Create Character
                            </button>

                            <button
                                className="dropdown-item"
                                onClick={() => { setMobileMenuOpen(false); onPhotoStudioClick(); }}
                            >
                                <span>📸</span> Photo Studio & Gallery
                            </button>

                            <button
                                className="dropdown-item vip-item"
                                onClick={() => { setMobileMenuOpen(false); onOpenVipModal(); }}
                            >
                                <span>💎</span> Upgrade to VIP Pro
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}

export default Header;