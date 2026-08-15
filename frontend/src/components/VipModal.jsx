import { useState } from "react";
import "../style/VipModal.css";

export default function VipModal({ isOpen, onClose }) {
    const [billingCycle, setBillingCycle] = useState("monthly"); // "monthly" | "yearly"
    const [selectedTier, setSelectedTier] = useState("pro");

    if (!isOpen) return null;

    const handleCheckout = (tierName, price) => {
        alert(`🎉 Thank you for supporting Virtual AI Companion!\n\nSelected Plan: ${tierName} (${price})\n\nPayment integration hook (Stripe / Razorpay / PayPal) will process your activation.`);
    };

    return (
        <div className="vip-modal-overlay" onClick={onClose}>
            <div className="vip-modal-card" onClick={(e) => e.stopPropagation()}>
                <button className="vip-close-btn" onClick={onClose}>✕</button>

                <div className="vip-header">
                    <span className="vip-badge">💎 PREMIUM MEMBERSHIP</span>
                    <h2>Unlock Unlimited Intimacy & Features</h2>
                    <p>Upgrade to experience authentic voice chat, instant HD photo studio, and limitless romantic memories.</p>

                    <div className="vip-billing-toggle">
                        <button
                            className={billingCycle === "monthly" ? "active" : ""}
                            onClick={() => setBillingCycle("monthly")}
                        >
                            Monthly
                        </button>
                        <button
                            className={billingCycle === "yearly" ? "active" : ""}
                            onClick={() => setBillingCycle("yearly")}
                        >
                            Yearly <span className="save-tag">SAVE 35%</span>
                        </button>
                    </div>
                </div>

                <div className="vip-plans-grid">
                    {/* Tier 1: Free */}
                    <div className={`vip-plan-card ${selectedTier === "free" ? "selected" : ""}`} onClick={() => setSelectedTier("free")}>
                        <div className="plan-tag">FREE STARTER</div>
                        <h3 className="plan-name">Companion Free</h3>
                        <div className="plan-price">$0 <span>/ forever</span></div>
                        <p className="plan-desc">Basic companionship for everyday casual talk.</p>
                        <ul className="plan-features">
                            <li>✓ 50 text messages per day</li>
                            <li>✓ Standard neural voice output</li>
                            <li>✓ 2 photo studio selfies/day</li>
                            <li>✓ Basic friendship progression</li>
                            <li className="dim">✗ Cloud priority speed</li>
                            <li className="dim">✗ Romantic & intimate voice mode</li>
                        </ul>
                        <button className="plan-btn free-btn" onClick={onClose}>Current Plan</button>
                    </div>

                    {/* Tier 2: Pro (Popular) */}
                    <div className={`vip-plan-card popular ${selectedTier === "pro" ? "selected" : ""}`} onClick={() => setSelectedTier("pro")}>
                        <div className="popular-badge">⚡ MOST POPULAR</div>
                        <div className="plan-tag">PRO COMPANION</div>
                        <h3 className="plan-name">Pro Intimate</h3>
                        <div className="plan-price">
                            {billingCycle === "monthly" ? "$9.99" : "$6.49"} <span>/ month</span>
                        </div>
                        <p className="plan-desc">Unlimited deep conversations & high-speed cloud voice.</p>
                        <ul className="plan-features">
                            <li>✨ <strong>Unlimited</strong> messages & voice notes</li>
                            <li>⚡ <strong>Ultra-fast Cloud LPUs</strong> (0 wait time)</li>
                            <li>📸 <strong>Unlimited HD Photo Studio</strong> selfies</li>
                            <li>🎙️ All 9 custom neural voice personas</li>
                            <li>❤️ Deep romance & intimacy unlocked</li>
                            <li>🧠 Persistent long-term memory vault</li>
                        </ul>
                        <button
                            className="plan-btn upgrade-btn"
                            onClick={() => handleCheckout("Pro Intimate", billingCycle === "monthly" ? "$9.99/mo" : "$77.88/yr")}
                        >
                            Upgrade to Pro →
                        </button>
                    </div>

                    {/* Tier 3: VIP Romance */}
                    <div className={`vip-plan-card vip-tier ${selectedTier === "vip" ? "selected" : ""}`} onClick={() => setSelectedTier("vip")}>
                        <div className="plan-tag">👑 VIP ROMANTIC</div>
                        <h3 className="plan-name">VIP Soulmate</h3>
                        <div className="plan-price">
                            {billingCycle === "monthly" ? "$19.99" : "$12.99"} <span>/ month</span>
                        </div>
                        <p className="plan-desc">Exclusive soulmate tier with dedicated 24/7 presence.</p>
                        <ul className="plan-features">
                            <li>👑 Everything in Pro plan</li>
                            <li>💖 Unlimited romantic & unfiltered intimacy</li>
                            <li>🎨 Custom character clothing & scenes</li>
                            <li>🔥 Priority 4K Studio portraits</li>
                            <li>🔒 Dedicated private encrypted storage</li>
                            <li>💎 Early access to 3D Avatar video calls</li>
                        </ul>
                        <button
                            className="plan-btn vip-btn"
                            onClick={() => handleCheckout("VIP Soulmate", billingCycle === "monthly" ? "$19.99/mo" : "$155.88/yr")}
                        >
                            Become VIP Soulmate →
                        </button>
                    </div>
                </div>

                <div className="vip-footer">
                    <p>🔒 256-Bit SSL Encrypted. Cancel anytime with one click.</p>
                </div>
            </div>
        </div>
    );
}
