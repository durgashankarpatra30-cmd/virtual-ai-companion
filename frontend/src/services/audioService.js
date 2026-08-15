import api, { getFullAssetUrl } from "./api";

// -------------------------------------------------------------
// 1. Live Speech Recognition (Web Speech API)
// -------------------------------------------------------------
export class SpeechRecognitionService {
    constructor() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.isSupported = !!SpeechRecognition;
        this.recognition = SpeechRecognition ? new SpeechRecognition() : null;
        this.isListening = false;

        if (this.recognition) {
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = "en-US";
        }
    }

    start({ onResult, onInterim, onEnd, onError, lang = "en-US" }) {
        if (!this.recognition) {
            if (onError) onError(new Error("Speech recognition is not supported in this browser."));
            return false;
        }

        try {
            this.recognition.lang = lang;
            this.recognition.onstart = () => {
                this.isListening = true;
            };

            this.recognition.onresult = (event) => {
                let interimTranscript = "";
                let finalTranscript = "";

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                if (interimTranscript && onInterim) {
                    onInterim(interimTranscript);
                }
                if (finalTranscript && onResult) {
                    onResult(finalTranscript);
                }
            };

            this.recognition.onerror = (event) => {
                console.warn("Speech recognition error:", event.error);
                if (onError) onError(event);
            };

            this.recognition.onend = () => {
                this.isListening = false;
                if (onEnd) onEnd();
            };

            this.recognition.start();
            return true;
        } catch (e) {
            console.error("Error starting speech recognition:", e);
            if (onError) onError(e);
            return false;
        }
    }

    stop() {
        if (this.recognition && this.isListening) {
            try {
                this.recognition.stop();
            } catch (e) {
                console.warn("Error stopping recognition:", e);
            }
            this.isListening = false;
        }
    }
}

// -------------------------------------------------------------
// 2. Microphone Audio Recorder (MediaRecorder + Audio Analyzer)
// -------------------------------------------------------------
export class AudioRecorderService {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.source = null;
        this.animFrameId = null;
        this.isRecording = false;
    }

    async start({ onVisualizerData, onError }) {
        try {
            this.audioChunks = [];
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                }
            });

            // Set up AudioContext for live frequency visualizer bars
            try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                this.audioContext = new AudioCtx();
                this.analyser = this.audioContext.createAnalyser();
                this.analyser.fftSize = 64;
                this.source = this.audioContext.createMediaStreamSource(this.audioStream);
                this.source.connect(this.analyser);

                if (onVisualizerData) {
                    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
                    const updateVisualizer = () => {
                        if (!this.isRecording) return;
                        this.analyser.getByteFrequencyData(dataArray);
                        // Normalize 0..100
                        const levels = Array.from(dataArray.slice(0, 12)).map(v => Math.round((v / 255) * 100));
                        onVisualizerData(levels);
                        this.animFrameId = requestAnimationFrame(updateVisualizer);
                    };
                    updateVisualizer();
                }
            } catch (vizErr) {
                console.warn("Web Audio visualizer setup failed:", vizErr);
            }

            const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
                ? "audio/webm;codecs=opus"
                : MediaRecorder.isTypeSupported("audio/webm")
                ? "audio/webm"
                : MediaRecorder.isTypeSupported("audio/mp4")
                ? "audio/mp4"
                : "";

            this.mediaRecorder = mimeType
                ? new MediaRecorder(this.audioStream, { mimeType })
                : new MediaRecorder(this.audioStream);

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.start(100);
            this.isRecording = true;
            return true;
        } catch (err) {
            console.error("Failed to start audio recording:", err);
            if (onError) onError(err);
            return false;
        }
    }

    async stop() {
        return new Promise((resolve) => {
            if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
                this.cleanup();
                resolve(null);
                return;
            }

            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.audioChunks, {
                    type: this.mediaRecorder.mimeType || "audio/webm"
                });
                const url = URL.createObjectURL(blob);
                this.cleanup();
                resolve({ blob, url });
            };

            try {
                this.mediaRecorder.stop();
            } catch (e) {
                this.cleanup();
                resolve(null);
            }
        });
    }

    cleanup() {
        this.isRecording = false;
        if (this.animFrameId) {
            cancelAnimationFrame(this.animFrameId);
            this.animFrameId = null;
        }
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        if (this.audioContext && this.audioContext.state !== "closed") {
            try {
                this.audioContext.close();
            } catch (e) {}
            this.audioContext = null;
        }
    }

    async uploadAudioBlob(blob) {
        if (!blob) return null;
        try {
            const formData = new FormData();
            const ext = blob.type.includes("mp4") ? "mp4" : "webm";
            formData.append("file", blob, `user_voice_${Date.now()}.${ext}`);
            const response = await api.post("/transcribe-audio", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });
            return response.data;
        } catch (err) {
            console.error("Audio upload error:", err);
            return null;
        }
    }
}

// -------------------------------------------------------------
// 3. Companion Audio Player & Speech Synthesis Manager
// -------------------------------------------------------------
class CompanionAudioManager {
    constructor() {
        this.currentAudio = null;
        this.currentTrackId = null;
        this.listeners = new Set();
        this.isSpeaking = false;
        this.playbackRate = 1.0;
        this.autoPlayEnabled = (localStorage.getItem("virtual_companion_voice_mode") ?? "true") === "true";
    }

    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    addListener(callback) {
        return this.subscribe(callback);
    }

    removeListener(callback) {
        this.listeners.delete(callback);
    }

    notify(state) {
        this.listeners.forEach(cb => {
            try { cb(state); } catch (e) {}
        });
    }

    setAutoPlay(enabled) {
        this.autoPlayEnabled = enabled;
        localStorage.setItem("virtual_companion_voice_mode", String(enabled));
        this.notify({ autoPlay: enabled });
    }

    getAutoPlay() {
        return this.autoPlayEnabled;
    }

    setPlaybackRate(rate) {
        this.playbackRate = rate;
        if (this.currentAudio) {
            this.currentAudio.playbackRate = rate;
        }
        this.notify({ playbackRate: rate });
    }

    stop() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        this.isSpeaking = false;
        this.currentTrackId = null;
        this.notify({ isSpeaking: false, currentTrackId: null, isPlaying: false, progress: 0 });
    }

    async play(audioUrl, trackId = null, onProgress = null) {
        if (!audioUrl) return;

        // If currently playing the same track, toggle pause/play
        if (this.currentTrackId === trackId && this.currentAudio) {
            if (!this.currentAudio.paused) {
                this.currentAudio.pause();
                this.isSpeaking = false;
                this.notify({ isSpeaking: false, isPlaying: false, currentTrackId: trackId });
                return;
            } else {
                this.currentAudio.play();
                this.isSpeaking = true;
                this.notify({ isSpeaking: true, isPlaying: true, currentTrackId: trackId });
                return;
            }
        }

        // Stop any current audio
        this.stop();

        const fullUrl = getFullAssetUrl(audioUrl);

        const audio = new Audio(fullUrl);
        audio.playbackRate = this.playbackRate;
        this.currentAudio = audio;
        this.currentTrackId = trackId;

        audio.ontimeupdate = () => {
            const duration = audio.duration || 1;
            const progress = (audio.currentTime / duration) * 100;
            const currentTime = audio.currentTime;
            if (onProgress) onProgress({ progress, currentTime, duration });
            this.notify({ progress, currentTime, duration, currentTrackId: trackId, isPlaying: true });
        };

        audio.onended = () => {
            this.isSpeaking = false;
            this.currentTrackId = null;
            this.currentAudio = null;
            this.notify({ isSpeaking: false, isPlaying: false, currentTrackId: null, progress: 100 });
        };

        audio.onerror = (err) => {
            console.warn("Audio playback error for URL:", fullUrl, err);
            this.isSpeaking = false;
            this.currentTrackId = null;
            this.currentAudio = null;
            this.notify({ isSpeaking: false, isPlaying: false, currentTrackId: null, error: err });
        };

        try {
            await audio.play();
            this.isSpeaking = true;
            this.notify({ isSpeaking: true, isPlaying: true, currentTrackId: trackId, audioUrl: fullUrl });
        } catch (e) {
            console.warn("Autoplay / Audio play was prevented or failed:", e);
            this.isSpeaking = false;
            this.notify({ isSpeaking: false, isPlaying: false, currentTrackId: trackId, error: e });
        }
    }

    // Client-side browser TTS fallback if needed
    speakTextFallback(text, gender = "Female") {
        if (!window.speechSynthesis) return;
        this.stop();

        const utterance = new SpeechSynthesisUtterance(text);
        const voices = window.speechSynthesis.getVoices();

        if (voices.length > 0) {
            const isMale = (gender || "").toLowerCase().includes("male") && !(gender || "").toLowerCase().includes("female");
            const preferred = voices.find(v =>
                v.lang.startsWith("en") && (isMale ? v.name.toLowerCase().includes("male") || v.name.toLowerCase().includes("guy") : v.name.toLowerCase().includes("female") || v.name.toLowerCase().includes("zira") || v.name.toLowerCase().includes("samantha"))
            ) || voices.find(v => v.lang.startsWith("en")) || voices[0];

            if (preferred) utterance.voice = preferred;
        }

        utterance.rate = this.playbackRate;
        utterance.onstart = () => {
            this.isSpeaking = true;
            this.notify({ isSpeaking: true, isPlaying: true, isFallback: true });
        };
        utterance.onend = () => {
            this.isSpeaking = false;
            this.notify({ isSpeaking: false, isPlaying: false });
        };
        utterance.onerror = () => {
            this.isSpeaking = false;
            this.notify({ isSpeaking: false, isPlaying: false });
        };

        window.speechSynthesis.speak(utterance);
    }
}

export const speechRecognitionService = new SpeechRecognitionService();
export const audioRecorderService = new AudioRecorderService();
export const companionAudioManager = new CompanionAudioManager();
