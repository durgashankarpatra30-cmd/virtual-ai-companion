import { useState, useEffect, useRef } from "react";
import { companionAudioManager } from "../services/audioService";
import api, { getFullAssetUrl } from "../services/api";
import "../style/Message.css";

function Message({ message, companion, index }) {
    const [isZoomed, setIsZoomed] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [playbackRate, setPlaybackRate] = useState(1.0);
    const [localAudioUrl, setLocalAudioUrl] = useState(message.audio || message.audio_url || null);
    const [isLoadingAudio, setIsLoadingAudio] = useState(false);

    const trackId = `msg_${message.id || index || Date.now()}`;

    // Subscribe to global audio manager events
    useEffect(() => {
        const unsubscribe = companionAudioManager.subscribe((state) => {
            if (state.currentTrackId === trackId) {
                if (typeof state.isPlaying === "boolean") setIsPlaying(state.isPlaying);
                if (typeof state.progress === "number") setProgress(state.progress);
                if (typeof state.currentTime === "number") setCurrentTime(state.currentTime);
                if (typeof state.duration === "number") setDuration(state.duration);
            } else if (state.currentTrackId !== trackId && isPlaying) {
                setIsPlaying(false);
                setProgress(0);
            }
        });
        return unsubscribe;
    }, [trackId, isPlaying]);

    const getImageUrl = () => {
        const raw = message.image || message.image_url || (message.image_data && message.image_data.url);
        if (!raw) return null;
        return getFullAssetUrl(raw);
    };

    const imageUrl = getImageUrl();
    const audioUrl = localAudioUrl || message.audio || (message.audio_data && message.audio_data.url);

    const formatSeconds = (sec) => {
        if (!sec || isNaN(sec)) return "0:00";
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s < 10 ? "0" : ""}${s}`;
    };

    const handleTogglePlay = async () => {
        if (audioUrl) {
            companionAudioManager.play(audioUrl, trackId);
            return;
        }

        // If message has text but no audio yet, request on-demand TTS synthesis
        if (!isUser && message.text) {
            setIsLoadingAudio(true);
            try {
                const res = await api.post("/tts", {
                    text: message.text,
                    voice_id: companion?.voice_id || "en-US-AriaNeural"
                });
                if (res.data && res.data.audio && res.data.audio.url) {
                    setLocalAudioUrl(res.data.audio.url);
                    companionAudioManager.play(res.data.audio.url, trackId);
                } else {
                    // Fallback to browser synthesis
                    companionAudioManager.speakTextFallback(message.text, companion?.gender);
                }
            } catch (err) {
                console.warn("TTS synthesis error:", err);
                companionAudioManager.speakTextFallback(message.text, companion?.gender);
            } finally {
                setIsLoadingAudio(false);
            }
        }
    };

    const cyclePlaybackRate = (e) => {
        e.stopPropagation();
        const nextRate = playbackRate === 1.0 ? 1.25 : playbackRate === 1.25 ? 1.5 : 1.0;
        setPlaybackRate(nextRate);
        companionAudioManager.setPlaybackRate(nextRate);
    };

    return (
        <div className={isUser ? "message user" : "message assistant"}>
            <div className="message-header">
                <span className="message-name">
                    {isUser ? "You" : companion?.name || "Companion"}
                    {message.is_voice && <span className="voice-badge">🎙️ Voice Note</span>}
                </span>
                <div className="message-header-right">
                    <span className="message-time">{message.time}</span>
                    {/* Speak on demand button */}
                    {!isUser && (
                        <button
                            type="button"
                            className={`speak-icon-btn ${isPlaying ? "playing" : ""}`}
                            onClick={handleTogglePlay}
                            title={isPlaying ? "Pause voice" : "Read aloud"}
                            disabled={isLoadingAudio}
                        >
                            {isLoadingAudio ? "⏳" : isPlaying ? "🔊" : "🔈"}
                        </button>
                    )}
                </div>
            </div>

            <div className="message-bubble">
                {imageUrl && (
                    <div className="message-image-wrap">
                        <img
                            src={imageUrl}
                            alt="Companion photo"
                            className="message-attached-img"
                            onClick={() => setIsZoomed(true)}
                            loading="lazy"
                        />
                        <div className="img-overlay-badge">
                            <span>📷 Click to view</span>
                        </div>
                    </div>
                )}

                {/* Voice Audio Player Bar */}
                {(audioUrl || isPlaying) && (
                    <div className={`message-audio-player ${isPlaying ? "is-playing" : ""}`}>
                        <button
                            type="button"
                            className="audio-play-btn"
                            onClick={handleTogglePlay}
                            title={isPlaying ? "Pause" : "Play voice"}
                        >
                            {isPlaying ? "⏸" : "▶"}
                        </button>

                        <div className="audio-wave-visualizer">
                            {[12, 24, 16, 32, 20, 28, 14, 22, 30, 18, 26, 15].map((h, i) => (
                                <span
                                    key={i}
                                    className={`audio-bar ${isPlaying ? "animating" : ""}`}
                                    style={{
                                        height: isPlaying ? `${Math.max(6, (h * (0.6 + Math.random() * 0.6)))}px` : `${Math.max(6, h * 0.45)}px`,
                                        animationDelay: `${i * 0.08}s`
                                    }}
                                />
                            ))}
                        </div>

                        <div className="audio-info">
                            <span className="audio-time">
                                {isPlaying && duration > 0
                                    ? `${formatSeconds(currentTime)} / ${formatSeconds(duration)}`
                                    : "Voice Note"}
                            </span>
                        </div>

                        <button
                            type="button"
                            className="audio-speed-btn"
                            onClick={cyclePlaybackRate}
                            title="Change playback speed"
                        >
                            {playbackRate}x
                        </button>
                    </div>
                )}

                {message.text && (
                    <div className="message-text">
                        {message.text}
                    </div>
                )}
            </div>

            {/* In-chat Lightbox for attached image */}
            {isZoomed && imageUrl && (
                <div className="chat-img-lightbox" onClick={() => setIsZoomed(false)}>
                    <div className="chat-lightbox-inner" onClick={(e) => e.stopPropagation()}>
                        <button className="chat-lightbox-close" onClick={() => setIsZoomed(false)}>✕</button>
                        <img src={imageUrl} alt="Enlarged view" />
                        <a
                            href={imageUrl}
                            download="companion_photo.jpg"
                            target="_blank"
                            rel="noreferrer"
                            className="chat-lightbox-download"
                        >
                            ⬇️ Download High-Res
                        </a>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Message;