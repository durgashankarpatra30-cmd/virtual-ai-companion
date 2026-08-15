import { useState, useEffect } from "react";
import api, { getFullAssetUrl } from "../services/api";
import "../style/PhotoModal.css";

const PRESETS = [
    {
        id: "selfie",
        label: "Casual Selfie 🤳",
        scene: "taking a casual selfie with a cute warm smile",
        mood: "Happy",
        icon: "🤳"
    },
    {
        id: "coffee",
        label: "Morning Coffee ☕",
        scene: "sitting in a cozy modern cafe holding a warm ceramic cup of coffee",
        mood: "Calm",
        icon: "☕"
    },
    {
        id: "reading",
        label: "Reading in Room 📖",
        scene: "relaxing on a plush sofa reading a novel with soft warm indoor lighting",
        mood: "Thoughtful",
        icon: "📖"
    },
    {
        id: "rain",
        label: "Rainy Window 🌧️",
        scene: "standing near a rain-streaked window looking outside gently",
        mood: "Peaceful",
        icon: "🌧️"
    },
    {
        id: "park",
        label: "Nature Walk 🌿",
        scene: "walking through a sunlit green park with cherry blossoms and gentle breeze",
        mood: "Cheerful",
        icon: "🌿"
    },
    {
        id: "evening",
        label: "Cozy Evening 🌙",
        scene: "relaxing in a softly lit bedroom with fairy lights in the background",
        mood: "Dreamy",
        icon: "🌙"
    }
];

const MOODS = ["Happy", "Gentle", "Playful", "Thoughtful", "Excited", "Calm", "Dreamy"];

function PhotoModal({ companion, onClose, onAvatarUpdated, onPhotoGenerated }) {
    const [tab, setTab] = useState("generate"); // 'generate' | 'gallery'
    const [selectedPreset, setSelectedPreset] = useState("selfie");
    const [customPrompt, setCustomPrompt] = useState("");
    const [selectedMood, setSelectedMood] = useState("Happy");
    const [setAsAvatar, setSetAsAvatar] = useState(true);

    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState("");
    const [latestGenerated, setLatestGenerated] = useState(null);
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);

    const companionName = companion?.name || "Companion";

    // Load history when modal opens or tab changes
    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        setLoadingHistory(true);
        try {
            const res = await api.get("/image-history");
            setHistory(res.data.history || []);
        } catch (err) {
            console.error("Failed to load photo history:", err);
        } finally {
            setLoadingHistory(false);
        }
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        setGenerationStatus("Dreaming up the scene & lighting...");

        const statusInterval = setInterval(() => {
            const messages = [
                "Applying facial details & style...",
                "Rendering photorealistic portrait...",
                "Adding fine textures and lighting...",
                "Almost ready..."
            ];
            setGenerationStatus((prev) => {
                const nextIdx = (messages.indexOf(prev) + 1) % messages.length;
                return messages[nextIdx];
            });
        }, 3000);

        try {
            let sceneText = customPrompt.trim();
            if (!sceneText) {
                const presetObj = PRESETS.find((p) => p.id === selectedPreset);
                sceneText = presetObj ? presetObj.scene : "taking a selfie";
            }

            const payload = {
                scene: sceneText,
                mood: selectedMood,
                is_avatar: setAsAvatar
            };

            const response = await api.post("/generate-image", payload);
            clearInterval(statusInterval);

            if (response.data && response.data.image) {
                const newImg = response.data.image;
                setLatestGenerated(newImg);
                setSelectedImage(newImg);
                setHistory((prev) => [newImg, ...prev]);

                if (setAsAvatar && onAvatarUpdated) {
                    onAvatarUpdated(newImg);
                }

                if (onPhotoGenerated) {
                    onPhotoGenerated(newImg);
                }
            }
        } catch (error) {
            clearInterval(statusInterval);
            console.error("Error generating image:", error);
            alert("Could not generate image. Please try again!");
        } finally {
            setIsGenerating(false);
            setGenerationStatus("");
        }
    };

    const handleSetAvatar = async (imageId) => {
        try {
            const res = await api.post("/companion/avatar/set", { image_id: imageId });
            if (res.data.success && onAvatarUpdated) {
                onAvatarUpdated(res.data.avatar);
                fetchHistory();
                alert("Profile avatar updated successfully! ✨");
            }
        } catch (err) {
            console.error("Failed to set avatar:", err);
        }
    };

    const getFullImageUrl = (relativeUrl) => {
        if (!relativeUrl) return "";
        return getFullAssetUrl(relativeUrl);
    };

    return (
        <div className="photo-modal-overlay">
            <div className="photo-modal-card">
                {/* Header */}
                <div className="photo-modal-header">
                    <div className="title-area">
                        <h2>📸 {companionName}&apos;s Photo Studio</h2>
                        <p>Generate high-quality photorealistic portraits and selfies</p>
                    </div>
                    <button className="photo-close-btn" onClick={onClose}>✕</button>
                </div>

                {/* Tabs */}
                <div className="photo-modal-tabs">
                    <button
                        className={`tab-btn ${tab === "generate" ? "active" : ""}`}
                        onClick={() => setTab("generate")}
                    >
                        ✨ Create New Photo
                    </button>
                    <button
                        className={`tab-btn ${tab === "gallery" ? "active" : ""}`}
                        onClick={() => {
                            setTab("gallery");
                            fetchHistory();
                        }}
                    >
                        🖼️ Photo Gallery ({history.length})
                    </button>
                </div>

                {/* Tab: Generate */}
                {tab === "generate" && (
                    <div className="photo-modal-body">
                        {/* Left: Controls */}
                        <div className="photo-controls">
                            <label className="section-label">Choose a Scene or Setting:</label>
                            <div className="presets-grid">
                                {PRESETS.map((preset) => (
                                    <div
                                        key={preset.id}
                                        className={`preset-card ${selectedPreset === preset.id && !customPrompt ? "selected" : ""}`}
                                        onClick={() => {
                                            setSelectedPreset(preset.id);
                                            setCustomPrompt("");
                                        }}
                                    >
                                        <span className="preset-icon">{preset.icon}</span>
                                        <span className="preset-title">{preset.label}</span>
                                    </div>
                                ))}
                            </div>

                            <label className="section-label">Or Custom Scene / Activity:</label>
                            <input
                                type="text"
                                className="custom-input"
                                placeholder="e.g. wearing an oversized sweater in a library..."
                                value={customPrompt}
                                onChange={(e) => setCustomPrompt(e.target.value)}
                            />

                            <label className="section-label">Mood / Expression:</label>
                            <div className="mood-chips">
                                {MOODS.map((m) => (
                                    <button
                                        key={m}
                                        type="button"
                                        className={`mood-chip ${selectedMood === m ? "active" : ""}`}
                                        onClick={() => setSelectedMood(m)}
                                    >
                                        {m}
                                    </button>
                                ))}
                            </div>

                            <div className="avatar-checkbox">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={setAsAvatar}
                                        onChange={(e) => setSetAsAvatar(e.target.checked)}
                                    />
                                    <span>Set as active companion profile avatar</span>
                                </label>
                            </div>

                            <button
                                className="generate-action-btn"
                                onClick={handleGenerate}
                                disabled={isGenerating}
                            >
                                {isGenerating ? (
                                    <span className="btn-loading">
                                        <span className="spinner"></span> Generating Photo...
                                    </span>
                                ) : (
                                    "✨ Generate Photo"
                                )}
                            </button>
                        </div>

                        {/* Right: Preview Area */}
                        <div className="photo-preview-box">
                            {isGenerating ? (
                                <div className="generating-placeholder">
                                    <div className="pulse-circle"></div>
                                    <h3>Generating {companionName}&apos;s Photo...</h3>
                                    <p className="status-text">{generationStatus}</p>
                                    <span className="generating-hint">This usually takes about 3-5 seconds</span>
                                </div>
                            ) : latestGenerated ? (
                                <div className="preview-result">
                                    <img
                                        src={getFullImageUrl(latestGenerated.url)}
                                        alt="Generated companion"
                                        className="preview-img"
                                    />
                                    <div className="preview-meta">
                                        <span className="scene-tag">{latestGenerated.scene || "Portrait"}</span>
                                        <span className="time-tag">{latestGenerated.created_at || "Just now"}</span>
                                    </div>
                                    <div className="preview-actions">
                                        <button
                                            className="set-avatar-btn"
                                            onClick={() => handleSetAvatar(latestGenerated.id)}
                                        >
                                            ⭐ Set as Profile Picture
                                        </button>
                                        <a
                                            href={getFullImageUrl(latestGenerated.url)}
                                            download={latestGenerated.filename || "companion.jpg"}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="download-btn"
                                        >
                                            ⬇️ Download
                                        </a>
                                    </div>
                                </div>
                            ) : (
                                <div className="empty-preview">
                                    <div className="empty-icon">📷</div>
                                    <h3>No Photo Generated Yet</h3>
                                    <p>Select a scene preset on the left and click &quot;Generate Photo&quot; to create a photorealistic portrait of {companionName}!</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Tab: Gallery */}
                {tab === "gallery" && (
                    <div className="gallery-view">
                        {loadingHistory ? (
                            <div className="gallery-loading">
                                <div className="spinner"></div>
                                <p>Loading memories...</p>
                            </div>
                        ) : history.length === 0 ? (
                            <div className="empty-preview">
                                <div className="empty-icon">🖼️</div>
                                <h3>No Photos in Gallery</h3>
                                <p>Generate your first photo of {companionName} to build your memory album!</p>
                            </div>
                        ) : (
                            <div className="gallery-grid">
                                {history.map((item) => (
                                    <div key={item.id} className="gallery-card">
                                        <div
                                            className="gallery-img-wrap"
                                            onClick={() => setSelectedImage(item)}
                                        >
                                            <img
                                                src={getFullImageUrl(item.url)}
                                                alt={item.scene || "Companion photo"}
                                                loading="lazy"
                                            />
                                            {item.is_avatar && <span className="avatar-badge">Active Avatar</span>}
                                        </div>
                                        <div className="gallery-info">
                                            <span className="gallery-scene">{item.scene || "Portrait"}</span>
                                            <span className="gallery-date">{item.created_at || ""}</span>
                                        </div>
                                        <button
                                            className="gallery-set-avatar-btn"
                                            onClick={() => handleSetAvatar(item.id)}
                                        >
                                            {item.is_avatar ? "✓ Current Avatar" : "Set as Avatar"}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Lightbox / Zoom View */}
            {selectedImage && (
                <div className="lightbox-overlay" onClick={() => setSelectedImage(null)}>
                    <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
                        <button className="lightbox-close" onClick={() => setSelectedImage(null)}>✕</button>
                        <img
                            src={getFullImageUrl(selectedImage.url)}
                            alt="Companion full preview"
                            className="lightbox-img"
                        />
                        <div className="lightbox-caption">
                            <h4>{selectedImage.scene || "Companion Portrait"}</h4>
                            <p>{selectedImage.created_at}</p>
                            <div className="lightbox-actions">
                                <button
                                    className="set-avatar-btn"
                                    onClick={() => handleSetAvatar(selectedImage.id)}
                                >
                                    ⭐ Set as Avatar
                                </button>
                                <a
                                    href={getFullImageUrl(selectedImage.url)}
                                    download={selectedImage.filename || "companion.jpg"}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="download-btn"
                                >
                                    ⬇️ Download High-Res
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default PhotoModal;
