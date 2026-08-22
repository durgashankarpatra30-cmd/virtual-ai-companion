import axios from "axios";
import { getUserId } from "./userSession";

export const API_BASE_URL =
    import.meta.env.VITE_API_URL ||
    (import.meta.env.PROD
        ? "https://virtual-ai-companion.onrender.com"
        : "http://127.0.0.1:8000");

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 60000, // 60s timeout for cloud wake-up & image generation
});

// Automatically attach unique User/Device ID to every request for complete isolation
api.interceptors.request.use((config) => {
    try {
        const userId = getUserId();
        if (userId) {
            config.headers["X-User-Id"] = userId;
        }
    } catch (e) {
        console.warn("Could not get user ID for request header:", e);
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

export const getFullAssetUrl = (url) => {
    if (!url) return "";
    if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("blob:") || url.startsWith("data:")) {
        return url;
    }
    const cleanBase = API_BASE_URL.replace(/\/$/, "");
    const cleanPath = url.startsWith("/") ? url : `/${url}`;
    return `${cleanBase}${cleanPath}`;
};

export default api;