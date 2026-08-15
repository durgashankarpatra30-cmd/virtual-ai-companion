import { useState, useEffect, useRef } from "react";
import { speechRecognitionService, audioRecorderService } from "../services/audioService";
import "../style/MessageInput.css";

function MessageInput({
    message,
    setMessage,
    sendMessage,
    companion,
    isTyping
}) {
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [interimText, setInterimText] = useState("");
    const [visualizerLevels, setVisualizerLevels] = useState([10, 20, 15, 30, 25, 40, 20, 15, 10]);
    const timerRef = useRef(null);

    const companionName = companion?.name || "your companion";

    useEffect(() => {
        if (isRecording) {
            setRecordingTime(0);
            timerRef.current = setInterval(() => {
                setRecordingTime((prev) => prev + 1);
            }, 1000);
        } else {
            if (timerRef.current) clearInterval(timerRef.current);
            setInterimText("");
        }
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [isRecording]);

    const formatTime = (secs) => {
        const m = Math.floor(secs / 60);
        const s = secs % 60;
        return `${m < 10 ? "0" : ""}${m}:${s < 10 ? "0" : ""}${s}`;
    };

    const handleKeyDown = (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            if (!isTyping && message.trim() !== "") {
                sendMessage();
            }
        }
    };

    // Start voice recording and live speech-to-text
    const startVoiceInput = async () => {
        if (isRecording) return;
        setIsRecording(true);
        setInterimText("");

        // 1. Start audio recorder with waveform visualizer
        await audioRecorderService.start({
            onVisualizerData: (levels) => {
                setVisualizerLevels(levels);
            },
            onError: (err) => {
                console.warn("Audio recorder error:", err);
            }
        });

        // 2. Start Web Speech API speech-to-text recognition
        speechRecognitionService.start({
            onInterim: (text) => {
                setInterimText(text);
            },
            onResult: (text) => {
                setMessage((prev) => {
                    const combined = prev ? `${prev.trim()} ${text}` : text;
                    return combined;
                });
                setInterimText("");
            },
            onError: (err) => {
                console.warn("Speech recognition error:", err);
            },
            onEnd: () => {
                // If recognition ends naturally, keep recording active until user cancels or sends
            }
        });
    };

    // Stop and send voice input
    const sendVoiceInput = async () => {
        speechRecognitionService.stop();
        const recorded = await audioRecorderService.stop();
        setIsRecording(false);

        const currentText = (message.trim() || interimText.trim());

        if (!currentText && !recorded) {
            return;
        }

        let userAudioUrl = null;
        if (recorded && recorded.blob) {
            // Upload user voice recording
            const uploadRes = await audioRecorderService.uploadAudioBlob(recorded.blob);
            if (uploadRes && uploadRes.url) {
                userAudioUrl = uploadRes.url;
            } else {
                userAudioUrl = recorded.url;
            }
        }

        const textToSend = currentText || "🎙️ [Voice Message]";
        sendMessage(textToSend, true, userAudioUrl);
        setMessage("");
        setInterimText("");
    };

    // Cancel voice recording
    const cancelVoiceInput = async () => {
        speechRecognitionService.stop();
        await audioRecorderService.stop();
        setIsRecording(false);
        setInterimText("");
    };

    return (
        <div className="message-input-wrapper">
            {/* Live speech preview overlay when recording */}
            {isRecording && (
                <div className="voice-recording-banner">
                    <div className="voice-status-left">
                        <span className="recording-dot"></span>
                        <span className="recording-time">{formatTime(recordingTime)}</span>
                        <div className="voice-wave-bars">
                            {visualizerLevels.slice(0, 8).map((lvl, idx) => (
                                <span
                                    key={idx}
                                    className="wave-bar"
                                    style={{
                                        height: `${Math.max(6, Math.min(28, lvl * 0.35))}px`,
                                        animationDelay: `${idx * 0.1}s`
                                    }}
                                />
                            ))}
                        </div>
                    </div>

                    <div className="voice-transcript-preview">
                        {interimText || message || "Listening to your voice... Speak clearly"}
                    </div>

                    <div className="voice-actions-right">
                        <button
                            type="button"
                            className="voice-cancel-btn"
                            onClick={cancelVoiceInput}
                            title="Cancel recording"
                        >
                            ✕
                        </button>
                        <button
                            type="button"
                            className="voice-send-btn"
                            onClick={sendVoiceInput}
                            title="Send voice message"
                        >
                            ✓ Send
                        </button>
                    </div>
                </div>
            )}

            <div className={`message-input-container ${isRecording ? "active-recording" : ""}`}>
                <input
                    type="text"
                    value={message}
                    placeholder={
                        isRecording
                            ? "Speaking... (Click ✓ or Send when finished)"
                            : `Message ${companionName}...`
                    }
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isRecording}
                />

                {/* Voice Input / Microphone Button */}
                {!isRecording ? (
                    <button
                        type="button"
                        className="mic-btn"
                        onClick={startVoiceInput}
                        title="Hold or click to speak (Voice Input)"
                    >
                        🎙️
                    </button>
                ) : (
                    <button
                        type="button"
                        className="mic-btn active-recording-btn"
                        onClick={sendVoiceInput}
                        title="Finish & Send voice"
                    >
                        ⏹️
                    </button>
                )}

                {/* Text Send Button */}
                <button
                    type="button"
                    className="send-btn"
                    onClick={() => {
                        if (isRecording) {
                            sendVoiceInput();
                        } else {
                            sendMessage();
                        }
                    }}
                    disabled={(!isRecording && message.trim() === "") || isTyping}
                    title="Send message"
                >
                    ➤
                </button>
            </div>
        </div>
    );
}

export default MessageInput;