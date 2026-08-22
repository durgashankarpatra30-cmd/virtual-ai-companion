// User Session & Device Profile Isolation Manager
// Ensures every user and device has its own private, isolated AI companion and chats

const USER_ID_KEY = "virtual_ai_companion_user_id";
const USER_NAME_KEY = "virtual_ai_companion_user_name";

/**
 * Generates a random unique ID for the device/user
 */
function generateUniqueId() {
    const timestamp = Date.now().toString(36);
    const randomPart = Math.random().toString(36).substring(2, 10);
    return `usr_${timestamp}_${randomPart}`;
}

/**
 * Retrieves the persistent unique user ID for this browser/device.
 * If none exists, creates and stores a new one.
 */
export function getUserId() {
    let userId = localStorage.getItem(USER_ID_KEY);
    if (!userId || typeof userId !== "string" || userId.trim() === "") {
        userId = generateUniqueId();
        localStorage.setItem(USER_ID_KEY, userId);
    }
    return userId.trim();
}

/**
 * Retrieves the optional custom user display name.
 */
export function getUserName() {
    return localStorage.getItem(USER_NAME_KEY) || "User";
}

/**
 * Updates the user's display name.
 */
export function setUserName(name) {
    if (name && typeof name === "string") {
        localStorage.setItem(USER_NAME_KEY, name.trim());
    }
}

/**
 * Resets the device session by generating a brand new unique user ID.
 * This effectively starts a completely fresh, isolated profile.
 */
export function resetUserSession() {
    const newId = generateUniqueId();
    localStorage.setItem(USER_ID_KEY, newId);
    return newId;
}

/**
 * Sets a specific existing user ID (for account restore / sync).
 */
export function setUserId(id) {
    if (id && typeof id === "string" && id.trim()) {
        localStorage.setItem(USER_ID_KEY, id.trim());
    }
}
