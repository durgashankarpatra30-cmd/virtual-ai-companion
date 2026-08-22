import { useState, useEffect, useRef } from "react";
import api, { getFullAssetUrl } from "../services/api";
import { companionAudioManager } from "../services/audioService";
import "../style/DateModal.css";

function DateModal({ companion, avatarUrl, isOpen, onClose, onDateCompleted }) {
    const [view, setView] = useState("lobby"); // "lobby" | "stage" | "summary" | "scrapbook"
    const [destinations, setDestinations] = useState([]);
    const [recommendedVenue, setRecommendedVenue] = useState(null);
    const [proactiveInvite, setProactiveInvite] = useState("");
    const [metrics, setMetrics] = useState({ affection: 50, trust: 45, comfort: 55, playfulness: 60 });
    const [selectedCategory, setSelectedCategory] = useState("all");
    
    // Active date session state
    const [activeSession, setActiveSession] = useState(null);
    const [sceneNarrative, setSceneNarrative] = useState("");
    const [companionDialogue, setCompanionDialogue] = useState("");
    const [choices, setChoices] = useState([]);
    const [turnCount, setTurnCount] = useState(0);
    const [canFinish, setCanFinish] = useState(false);
    const [activeMinigame, setActiveMinigame] = useState(null);
    const [pointsGained, setPointsGained] = useState({ affection: 0, trust: 0, comfort: 0, playfulness: 0 });
    const [floatingPoints, setFloatingPoints] = useState([]);
    const [customInput, setCustomInput] = useState("");
    const [isLoadingAction, setIsLoadingAction] = useState(false);

    // End-of-Date Summary
    const [memoryCard, setMemoryCard] = useState(null);
    const [rating, setRating] = useState("Amazing");
    const [allMemories, setAllMemories] = useState([]);
    const [scrapbookTab, setScrapbookTab] = useState("all");

    const stageEndRef = useRef(null);

    // Fetch destinations and history on open
    useEffect(() => {
        if (!isOpen) return;

        const fetchDestinations = async () => {
            try {
                const res = await api.get("/date/destinations");
                if (res.data) {
                    setDestinations(res.data.destinations || []);
                    setMetrics(res.data.metrics || { affection: 50, trust: 45, comfort: 55, playfulness: 60 });
                    setRecommendedVenue(res.data.recommended_venue);
                    setProactiveInvite(res.data.proactive_invite);
                }
            } catch (err) {
                console.error("Error loading date destinations:", err);
            }
        };

        const fetchHistory = async () => {
            try {
                const res = await api.get("/date/history");
                if (res.data && res.data.memories) {
                    setAllMemories(res.data.memories);
                }
            } catch (err) {
                console.error("Error loading date history:", err);
            }
        };

        fetchDestinations();
        fetchHistory();
    }, [isOpen]);

    // Auto-scroll inside stage dialogue
    useEffect(() => {
        if (view === "stage" && stageEndRef.current) {
            stageEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [companionDialogue, choices, activeMinigame, view]);

    if (!isOpen) return null;

    const companionName = companion?.name || "Companion";
    const relMode = companion?.relationship_mode || companion?.relationship?.relationship_mode || "friendship";
    const titleLabel = relMode === "lover" ? "Romantic Date Night" : relMode === "mentor" ? "Strategy & Mentorship Session" : "Bestie Adventure Hangout";

    // -------------------------------------------------------------
    // Start Date Action
    // -------------------------------------------------------------
    const handleStartVenue = async (venueId) => {
        setIsLoadingAction(true);
        try {
            const res = await api.post("/date/start", { venue_id: venueId });
            if (res.data) {
                setActiveSession(res.data);
                setSceneNarrative(res.data.narrative);
                setCompanionDialogue(res.data.greeting);
                setChoices(res.data.choices || []);
                setTurnCount(0);
                setCanFinish(false);
                setActiveMinigame(null);
                setPointsGained({ affection: 0, trust: 0, comfort: 0, playfulness: 0 });
                if (res.data.metrics) setMetrics(res.data.metrics);
                setView("stage");

                // Speak greeting if voice enabled
                if (res.data.greeting) {
                    companionAudioManager.speakTextFallback(res.data.greeting, companion?.gender);
                }
            }
        } catch (err) {
            console.error("Error starting date:", err);
        } finally {
            setIsLoadingAction(false);
        }
    };

    // -------------------------------------------------------------
    // Pick Choice or Send Custom Message
    // -------------------------------------------------------------
    const handlePickChoice = async (choiceId, customText = null) => {
        if (!activeSession || isLoadingAction) return;
        setIsLoadingAction(true);
        try {
            const payload = {
                session_id: activeSession.session_id,
                choice_id: choiceId,
                message: customText || customInput.trim() || undefined
            };

            const res = await api.post("/date/action", payload);
            if (res.data) {
                setCompanionDialogue(res.data.companion_reply);
                setChoices(res.data.next_choices || []);
                setTurnCount(res.data.turn_count || turnCount + 1);
                setCanFinish(res.data.can_finish || false);
                if (res.data.minigame) setActiveMinigame(res.data.minigame);
                if (res.data.metrics) setMetrics(res.data.metrics);
                if (res.data.total_points_gained) setPointsGained(res.data.total_points_gained);

                // Show floating points animation
                if (res.data.points_boost) {
                    const floater = Object.entries(res.data.points_boost)
                        .map(([k, v]) => `+${v} ${k.charAt(0).toUpperCase() + k.slice(1)}`)
                        .join(" • ");
                    setFloatingPoints((prev) => [...prev, { id: Date.now(), text: floater }]);
                    setTimeout(() => {
                        setFloatingPoints((prev) => prev.slice(1));
                    }, 2500);
                }

                setCustomInput("");

                // Speak reply aloud
                if (res.data.companion_reply) {
                    companionAudioManager.speakTextFallback(res.data.companion_reply, companion?.gender);
                }
            }
        } catch (err) {
            console.error("Error executing date action:", err);
        } finally {
            setIsLoadingAction(false);
        }
    };

    // -------------------------------------------------------------
    // Conclude Date Session
    // -------------------------------------------------------------
    const handleFinishDate = async () => {
        if (!activeSession || isLoadingAction) return;
        setIsLoadingAction(true);
        try {
            const res = await api.post("/date/finish", {
                session_id: activeSession.session_id,
                rating: rating
            });
            if (res.data && res.data.memory_card) {
                setMemoryCard(res.data.memory_card);
                setAllMemories(res.data.all_memories || []);
                if (res.data.metrics) setMetrics(res.data.metrics);
                setView("summary");

                if (onDateCompleted) {
                    onDateCompleted(res.data.memory_card);
                }
            }
        } catch (err) {
            console.error("Error concluding date:", err);
        } finally {
            setIsLoadingAction(false);
        }
    };

    const getAvatarSrc = () => {
        const url = avatarUrl || companion?.avatar_url || companion?.avatar?.url;
        if (!url) return null;
        return getFullAssetUrl(url);
    };

    const avatarSrc = getAvatarSrc();

    const filteredDestinations = selectedCategory === "all"
        ? destinations
        : destinations.filter((d) => d.category === selectedCategory);

    return (
        <div className="date-modal-backdrop" onClick={(e) => e.target.classList.contains("date-modal-backdrop") && onClose()}>
            <div className="date-modal-container">
                {/* Top Navigation Header */}
                <div className="date-modal-header">
                    <div className="date-header-left">
                        <span className="date-header-icon">🌹</span>
                        <div>
                            <h2 className="date-header-title">{titleLabel}</h2>
                            <p className="date-header-sub">Interactive Activities with {companionName}</p>
                        </div>
                    </div>

                    <div className="date-header-nav">
                        <button
                            className={`date-nav-pill ${view === "lobby" ? "active" : ""}`}
                            onClick={() => setView("lobby")}
                        >
                            📍 Venues
                        </button>
                        <button
                            className={`date-nav-pill ${view === "scrapbook" ? "active" : ""}`}
                            onClick={() => setView("scrapbook")}
                        >
                            📸 Scrapbook ({allMemories.length})
                        </button>
                        <button className="date-close-btn" onClick={onClose}>✕</button>
                    </div>
                </div>

                {/* Real-time Relationship Metric HUD */}
                <div className="date-metrics-hud">
                    <div className="hud-stat-chip">
                        <span className="hud-icon">❤️</span>
                        <div className="hud-info">
                            <div className="hud-label-row">
                                <span>Affection</span>
                                <strong>{metrics.affection}%</strong>
                            </div>
                            <div className="hud-bar"><div className="hud-fill affection" style={{ width: `${metrics.affection}%` }}></div></div>
                        </div>
                    </div>

                    <div className="hud-stat-chip">
                        <span className="hud-icon">🤝</span>
                        <div className="hud-info">
                            <div className="hud-label-row">
                                <span>Trust</span>
                                <strong>{metrics.trust}%</strong>
                            </div>
                            <div className="hud-bar"><div className="hud-fill trust" style={{ width: `${metrics.trust}%` }}></div></div>
                        </div>
                    </div>

                    <div className="hud-stat-chip">
                        <span className="hud-icon">☕</span>
                        <div className="hud-info">
                            <div className="hud-label-row">
                                <span>Comfort</span>
                                <strong>{metrics.comfort}%</strong>
                            </div>
                            <div className="hud-bar"><div className="hud-fill comfort" style={{ width: `${metrics.comfort}%` }}></div></div>
                        </div>
                    </div>

                    <div className="hud-stat-chip">
                        <span className="hud-icon">✨</span>
                        <div className="hud-info">
                            <div className="hud-label-row">
                                <span>Playfulness</span>
                                <strong>{metrics.playfulness}%</strong>
                            </div>
                            <div className="hud-bar"><div className="hud-fill playfulness" style={{ width: `${metrics.playfulness}%` }}></div></div>
                        </div>
                    </div>
                </div>

                {/* VIEW 1: LOBBY (DESTINATIONS) */}
                {view === "lobby" && (
                    <div className="date-lobby-view">
                        {/* Proactive Companion Invite Banner */}
                        {proactiveInvite && recommendedVenue && (
                            <div className="date-invite-banner" style={{ background: recommendedVenue.bg_theme }}>
                                <div className="invite-avatar-col">
                                    {avatarSrc ? (
                                        <img src={avatarSrc} alt={companionName} className="invite-avatar-img" />
                                    ) : (
                                        <div className="invite-avatar-placeholder">🌸</div>
                                    )}
                                </div>
                                <div className="invite-content-col">
                                    <span className="invite-badge">💌 {companionName}'s Special Invitation</span>
                                    <p className="invite-text">"{proactiveInvite}"</p>
                                    <button
                                        className="invite-accept-btn"
                                        onClick={() => handleStartVenue(recommendedVenue.id)}
                                    >
                                        ✨ Let's Go to {recommendedVenue.name}!
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Category Filter Chips */}
                        <div className="venue-filter-row">
                            {["all", "romantic", "cozy", "fun", "adventure"].map((cat) => (
                                <button
                                    key={cat}
                                    className={`venue-filter-chip ${selectedCategory === cat ? "active" : ""}`}
                                    onClick={() => setSelectedCategory(cat)}
                                >
                                    {cat.toUpperCase()}
                                </button>
                            ))}
                        </div>

                        {/* Destination Cards Grid */}
                        <div className="venue-cards-grid">
                            {filteredDestinations.map((v) => (
                                <div
                                    key={v.id}
                                    className="venue-card"
                                    onClick={() => handleStartVenue(v.id)}
                                >
                                    <div className="venue-card-bg" style={{ background: v.bg_theme }}>
                                        <span className="venue-card-icon">{v.icon}</span>
                                        <span className="venue-ambient-badge">{v.ambient_badge}</span>
                                    </div>
                                    <div className="venue-card-body">
                                        <h3 className="venue-title">{v.name}</h3>
                                        <p className="venue-desc">{v.tagline}</p>
                                        <button className="venue-start-btn">
                                            Start Date ➜
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* VIEW 2: INTERACTIVE VISUAL STAGE */}
                {view === "stage" && activeSession && (
                    <div
                        className="date-stage-view"
                        style={{ background: activeSession.venue.bg_theme }}
                    >
                        {/* Floating Gain Notifications */}
                        <div className="floating-notifications-container">
                            {floatingPoints.map((fp) => (
                                <div key={fp.id} className="floating-point-chip">
                                    💖 {fp.text}
                                </div>
                            ))}
                        </div>

                        {/* Stage Atmosphere Header */}
                        <div className="stage-scene-banner">
                            <span className="scene-icon">{activeSession.venue.icon}</span>
                            <div className="scene-details">
                                <strong>{activeSession.venue.name}</strong>
                                <p>{sceneNarrative}</p>
                            </div>
                            <span className="stage-turn-tag">Turn {turnCount + 1}</span>
                        </div>

                        {/* Companion Avatar & Dialogue Bubble */}
                        <div className="stage-character-row">
                            <div className="stage-avatar-wrapper">
                                {avatarSrc ? (
                                    <img src={avatarSrc} alt={companionName} className="stage-avatar-img" />
                                ) : (
                                    <div className="stage-avatar-fallback">✨</div>
                                )}
                                <span className="stage-avatar-name">{companionName}</span>
                            </div>

                            <div className="stage-speech-bubble">
                                <p className="bubble-text">{companionDialogue}</p>
                            </div>
                        </div>

                        {/* Mini-Game Overlay if active */}
                        {activeMinigame && (
                            <div className="minigame-card-widget">
                                <div className="minigame-header">
                                    <h4>{activeMinigame.title}</h4>
                                    <p>{activeMinigame.prompt}</p>
                                </div>

                                {activeMinigame.type === "truth_or_dare" && (
                                    <div className="minigame-options-row">
                                        {activeMinigame.options.map((opt, idx) => (
                                            <button
                                                key={idx}
                                                className="minigame-choice-btn"
                                                onClick={() => handlePickChoice(null, `[${opt.label}]: ${opt.question}`)}
                                            >
                                                <strong>{opt.label}</strong>
                                                <span>{opt.question}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {activeMinigame.type === "would_you_rather" && (
                                    <div className="minigame-options-row">
                                        <button
                                            className="minigame-choice-btn"
                                            onClick={() => handlePickChoice(null, `I'd choose: ${activeMinigame.option_a}`)}
                                        >
                                            {activeMinigame.option_a}
                                        </button>
                                        <span className="or-divider">OR</span>
                                        <button
                                            className="minigame-choice-btn"
                                            onClick={() => handlePickChoice(null, `I'd choose: ${activeMinigame.option_b}`)}
                                        >
                                            {activeMinigame.option_b}
                                        </button>
                                    </div>
                                )}

                                {activeMinigame.type === "two_truths" && (
                                    <div className="minigame-options-column">
                                        {activeMinigame.options.map((opt) => (
                                            <button
                                                key={opt.id}
                                                className="minigame-choice-btn"
                                                onClick={() => handlePickChoice(null, `I think the LIE is: "${opt.text}"`)}
                                            >
                                                <span>{opt.text}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Branching Action Choices */}
                        <div className="stage-choices-container">
                            <span className="choices-heading">What do you want to do next?</span>
                            <div className="choices-grid">
                                {choices.map((ch) => (
                                    <button
                                        key={ch.id}
                                        className="stage-choice-chip"
                                        disabled={isLoadingAction}
                                        onClick={() => handlePickChoice(ch.id, ch.text)}
                                    >
                                        {ch.text}
                                    </button>
                                ))}
                            </div>

                            {/* Free-form Custom Text Input */}
                            <form
                                className="stage-custom-input-row"
                                onSubmit={(e) => {
                                    e.preventDefault();
                                    if (customInput.trim()) handlePickChoice(null, customInput.trim());
                                }}
                            >
                                <input
                                    type="text"
                                    placeholder={`Say or do anything with ${companionName}...`}
                                    value={customInput}
                                    onChange={(e) => setCustomInput(e.target.value)}
                                    disabled={isLoadingAction}
                                />
                                <button type="submit" disabled={!customInput.trim() || isLoadingAction}>
                                    {isLoadingAction ? "..." : "Send 💬"}
                                </button>
                            </form>
                        </div>

                        {/* Wrap up & Date Finish Button */}
                        {canFinish && (
                            <div className="stage-finish-bar">
                                <button className="stage-finish-btn" onClick={handleFinishDate}>
                                    🌙 Wrap Up Date & Collect Memory Card ➜
                                </button>
                            </div>
                        )}

                        <div ref={stageEndRef} />
                    </div>
                )}

                {/* VIEW 3: END-OF-DATE SUMMARY (POLAROID MEMORY CARD) */}
                {view === "summary" && memoryCard && (
                    <div className="date-summary-view">
                        <div className="memory-card-polaroid" style={{ borderTop: `6px solid #e11d48` }}>
                            <div className="polaroid-header">
                                <span className="polaroid-date-badge">DATE #{memoryCard.date_number}</span>
                                <span className="polaroid-venue-title">{memoryCard.venue_icon} {memoryCard.venue_name}</span>
                            </div>

                            <div className="polaroid-highlight-box">
                                <span className="polaroid-label">♡ FAVORITE MOMENT</span>
                                <p className="polaroid-quote">"{memoryCard.highlight_moment}"</p>
                            </div>

                            <div className="polaroid-stats-grid">
                                <div className="polaroid-stat-item">
                                    <span className="p-label">🎵 Theme Song</span>
                                    <span className="p-val">{memoryCard.song}</span>
                                </div>
                                <div className="polaroid-stat-item">
                                    <span className="p-label">💬 Inside Joke</span>
                                    <span className="p-val">{memoryCard.inside_joke}</span>
                                </div>
                                <div className="polaroid-stat-item">
                                    <span className="p-label">❤️ Bond Gained</span>
                                    <span className="p-val gain">+{memoryCard.total_bond_gained} PTS</span>
                                </div>
                                <div className="polaroid-stat-item">
                                    <span className="p-label">📅 Recorded</span>
                                    <span className="p-val">{memoryCard.created_at}</span>
                                </div>
                            </div>

                            {/* End of Date Rating Selector */}
                            <div className="date-rating-section">
                                <span className="rating-heading">How was your date today?</span>
                                <div className="rating-options-row">
                                    {[
                                        { val: "Amazing", emoji: "❤️", text: "Amazing" },
                                        { val: "Really Good", emoji: "😊", text: "Great" },
                                        { val: "Nice", emoji: "🙂", text: "Nice" },
                                    ].map((r) => (
                                        <button
                                            key={r.val}
                                            className={`rating-btn ${rating === r.val ? "selected" : ""}`}
                                            onClick={() => setRating(r.val)}
                                        >
                                            <span className="r-emoji">{r.emoji}</span>
                                            <span className="r-text">{r.text}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="summary-actions-row">
                            <button
                                className="summary-album-btn"
                                onClick={() => setView("scrapbook")}
                            >
                                📸 View Scrapbook Album
                            </button>
                            <button
                                className="summary-close-btn"
                                onClick={onClose}
                            >
                                ✨ Return to Chat
                            </button>
                        </div>
                    </div>
                )}

                {/* VIEW 4: SCRAPBOOK GALLERY */}
                {view === "scrapbook" && (
                    <div className="date-scrapbook-view">
                        <div className="scrapbook-intro">
                            <h3>📸 Memory Scrapbook</h3>
                            <p>All the magical moments and milestones you and {companionName} have shared.</p>
                        </div>

                        {allMemories.length === 0 ? (
                            <div className="scrapbook-empty-state">
                                <span>🌸</span>
                                <h4>No Dates Yet!</h4>
                                <p>Go on your first date with {companionName} to start collecting memorable cards!</p>
                                <button className="start-first-btn" onClick={() => setView("lobby")}>
                                    🌹 Choose a Date Location
                                </button>
                            </div>
                        ) : (
                            <div className="scrapbook-cards-grid">
                                {allMemories.map((m, idx) => (
                                    <div key={m.id || idx} className="scrapbook-card-item">
                                        <div className="card-item-top">
                                            <span className="card-number">DATE #{m.date_number || idx + 1}</span>
                                            <span className="card-venue">{m.venue_icon} {m.venue_name}</span>
                                        </div>
                                        <p className="card-item-moment">"{m.highlight_moment}"</p>
                                        <div className="card-item-footer">
                                            <span className="card-joke">{m.inside_joke}</span>
                                            <span className="card-bond">+{m.total_bond_gained || 25} Bond</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default DateModal;
