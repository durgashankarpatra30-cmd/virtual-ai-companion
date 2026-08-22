import { useState, useEffect } from "react";
import api from "./services/api";
import { companionAudioManager } from "./services/audioService";

import Header from "./components/Header";
import MessageInput from "./components/MessageInput";
import Chatwindow from "./components/Chatwindow";
import CompanionProfile from "./components/CompanionProfile";
import PhotoModal from "./components/PhotoModal";
import WelcomeModal from "./components/WelcomeModal";
import VipModal from "./components/VipModal";
import "./App.css";

function App() {
    // Current text in input
    const [message, setMessage] = useState("");

    // Entire chat history
    const [messages, setMessages] = useState([]);

    // Companion information
    const [companion, setCompanion] = useState(null);

    // Companion active avatar URL
    const [avatarUrl, setAvatarUrl] = useState(null);

    // Auto-play Voice output mode toggle
    const [voiceMode, setVoiceMode] = useState(companionAudioManager.getAutoPlay());

    const [isTyping, setIsTyping] = useState(false);

    const [showProfile, setShowProfile] = useState(false);
    const [showPhotoModal, setShowPhotoModal] = useState(false);
    const [showWelcomeModal, setShowWelcomeModal] = useState(false);
    const [showVipModal, setShowVipModal] = useState(false);
    const [welcomeCanClose, setWelcomeCanClose] = useState(false);

    // Sync with AudioManager autoPlay changes
    useEffect(() => {
        const unsubscribe = companionAudioManager.subscribe((state) => {
            if (typeof state.autoPlay === "boolean") {
                setVoiceMode(state.autoPlay);
            }
        });
        return unsubscribe;
    }, []);

    // Runs only once when page loads
    useEffect(() => {
        const fetchCompanion = async () => {
            try {
                const response = await api.get("/companion");
                if (response.data && response.data.exists === true && response.data.name) {
                    setCompanion(response.data);
                    if (response.data.avatar_url) {
                        setAvatarUrl(response.data.avatar_url);
                    } else if (response.data.avatar && response.data.avatar.url) {
                        setAvatarUrl(response.data.avatar.url);
                    }
                    // Directly open chat with existing companion!
                    setShowWelcomeModal(false);
                } else {
                    // No companion yet on this device -> show creator modal
                    setShowWelcomeModal(true);
                }
            } catch (error) {
                console.error("Error loading companion:", error);
                setShowWelcomeModal(true);
            }
        };

        const fetchHistory = async () => {
            try {
                const response = await api.get("/history");
                const formatted = (response.data || []).map((m, idx) => ({
                    id: idx,
                    sender: m.role,
                    text: m.message,
                    image: m.image || (m.image_data && m.image_data.url) || null,
                    audio: m.audio || (m.audio_data && m.audio_data.url) || null,
                    is_voice: m.is_voice || false,
                    time: m.time || new Date(m.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }));
                setMessages(formatted);
            } catch (error) {
                console.error("Error loading history:", error);
            }
        };

        fetchCompanion();
        fetchHistory();
    }, []);

    const toggleVoiceMode = () => {
        const nextMode = !voiceMode;
        setVoiceMode(nextMode);
        companionAudioManager.setAutoPlay(nextMode);
    };

    // Send message (text or voice) to backend
    const sendMessage = async (overrideText, isVoice = false, userAudioUrl = null) => {
        const textToSend = typeof overrideText === "string" ? overrideText : message;
        if (!textToSend || textToSend.trim() === "") return;

        const userMessage = textToSend.trim();

        // Add user's message immediately
        const userMsgObj = {
            sender: "user",
            text: userMessage,
            is_voice: isVoice,
            audio: userAudioUrl,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages((prevMessages) => [...prevMessages, userMsgObj]);
        setIsTyping(true);

        // Clear input
        setMessage("");

        try {
            const response = await api.post("/chat", {
                message: userMessage,
                is_voice: isVoice,
                user_audio_url: userAudioUrl
            });

            console.log("Response from backend:", response.data);

            const aiReplyText = response.data.reply;
            const aiImage = response.data.image || (response.data.image_data && response.data.image_data.url);
            const aiAudio = response.data.audio || (response.data.audio_data && response.data.audio_data.url);

            const assistantMsgObj = {
                sender: "assistant",
                text: aiReplyText,
                image: aiImage,
                audio: aiAudio,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };

            // Add AI reply
            setMessages((prevMessages) => [...prevMessages, assistantMsgObj]);
            setIsTyping(false);

            // If Auto-play Voice Mode is active, play companion's voice aloud
            if (voiceMode) {
                if (aiAudio) {
                    companionAudioManager.play(aiAudio, `msg-${Date.now()}`);
                } else if (aiReplyText) {
                    companionAudioManager.speakTextFallback(aiReplyText, companion?.gender);
                }
            }

            if (response.data.companion) {
                setCompanion({
                    ...response.data.companion,
                    relationship: response.data.relationship
                });
            }

            if (response.data.avatar && response.data.avatar.url) {
                setAvatarUrl(response.data.avatar.url);
            }
        } catch (error) {
            console.error("Chat error:", error);

            setMessages((prevMessages) => [
                ...prevMessages,
                {
                    sender: "assistant",
                    text: "Unable to connect to backend.",
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            ]);
            setIsTyping(false);
        }
    };

    const handleAvatarUpdated = (newAvatar) => {
        if (newAvatar && newAvatar.url) {
            setAvatarUrl(newAvatar.url);
        }
    };

    const handlePhotoGenerated = (newPhoto) => {
        if (newPhoto && newPhoto.url) {
            setMessages((prev) => [
                ...prev,
                {
                    sender: "assistant",
                    text: `I just generated a new photo: "${newPhoto.scene || 'Portrait'}"! 📷✨`,
                    image: newPhoto.url,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            ]);
        }
    };

    const handleContinueExisting = () => {
        setShowWelcomeModal(false);
    };

    const handleCompanionCreated = (newCompanion, newAvatar) => {
        setCompanion(newCompanion);
        if (newAvatar && newAvatar.url) {
            setAvatarUrl(newAvatar.url);
        } else {
            setAvatarUrl(null);
        }

        const mode = newCompanion.relationship_mode || "friendship";
        let greetingText;
        if (mode === "mentor") {
            greetingText = `Greetings. I am ${newCompanion.name}, your mentor and advisor. I look forward to working together to accomplish your goals. What shall we focus on first?`;
        } else if (mode === "lover") {
            greetingText = `Hi sweetheart! I'm ${newCompanion.name}. I'm so happy to finally be here with you! How are you feeling today, my love? 🥰`;
        } else {
            greetingText = `Hey there! I'm ${newCompanion.name}. It's so awesome to meet you! How's your day going? 😊`;
        }

        setMessages([
            {
                sender: "assistant",
                text: greetingText,
                image: newAvatar?.url || null,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
        ]);

        setShowWelcomeModal(false);

        // Speak greeting if voice mode is on
        if (voiceMode) {
            companionAudioManager.speakTextFallback(greetingText, newCompanion.gender);
        }
    };

    return (
        <div className="app">
            <Header
                companion={companion}
                avatarUrl={avatarUrl}
                voiceMode={voiceMode}
                onToggleVoiceMode={toggleVoiceMode}
                onProfileClick={() => setShowProfile(true)}
                onPhotoStudioClick={() => setShowPhotoModal(true)}
                onNewCharacterClick={() => {
                    setWelcomeCanClose(true);
                    setShowWelcomeModal(true);
                }}
                onOpenVipModal={() => setShowVipModal(true)}
            />

            {/* VIP & Monetization Modal */}
            <VipModal
                isOpen={showVipModal}
                onClose={() => setShowVipModal(false)}
            />

            {/* Opening Welcome & Character Creator Modal */}
            {showWelcomeModal && (
                <WelcomeModal
                    existingCompanion={companion}
                    avatarUrl={avatarUrl}
                    onContinueExisting={handleContinueExisting}
                    onCompanionCreated={handleCompanionCreated}
                    canClose={welcomeCanClose}
                    onClose={() => setShowWelcomeModal(false)}
                />
            )}

            {showProfile && (
                <CompanionProfile
                    companion={companion}
                    avatarUrl={avatarUrl}
                    onClose={() => setShowProfile(false)}
                    onOpenPhotoStudio={() => setShowPhotoModal(true)}
                    onOpenNewCharacter={() => {
                        setShowProfile(false);
                        setWelcomeCanClose(true);
                        setShowWelcomeModal(true);
                    }}
                    onCompanionUpdated={(updated) => setCompanion(updated)}
                />
            )}

            {showPhotoModal && (
                <PhotoModal
                    companion={companion}
                    onClose={() => setShowPhotoModal(false)}
                    onAvatarUpdated={handleAvatarUpdated}
                    onPhotoGenerated={handlePhotoGenerated}
                />
            )}

            <div className="chat-container">
                <Chatwindow
                    messages={messages}
                    companion={companion}
                    isTyping={isTyping}
                />

                <MessageInput
                    message={message}
                    setMessage={setMessage}
                    sendMessage={sendMessage}
                    companion={companion}
                    isTyping={isTyping}
                />
            </div>
        </div>
    );
}

export default App;