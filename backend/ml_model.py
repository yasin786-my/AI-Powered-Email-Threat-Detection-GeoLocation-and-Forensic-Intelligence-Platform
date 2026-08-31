"""
Module 1: XGBoost Fraud Detection Model — Inference
Loads a pre-trained model and predicts fraud score from feature vectors.
"""

import os
import xgboost as xgb
import pandas as pd
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "fraud_model.json")

FEATURE_COLUMNS = [
    "spf_pass", "dkim_pass", "dmarc_aligned",
    "reply_to_mismatch", "return_path_mismatch",
    "sender_domain_age_days", "num_urls", "url_domain_mismatch",
    "urgency_word_count", "has_attachment",
    "sender_ip_is_vpn_hosting", "subject_length", "body_length"
]

# Lazy-loaded model singleton
_model = None


def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. "
                "Run train_model.py first to train the XGBoost model."
            )
        _model = xgb.XGBClassifier()
        _model.load_model(MODEL_PATH)
    return _model


def build_feature_vector(header_data, geo_data):
    """
    Build a feature vector from Module 2 (header) and Module 3 (geo) outputs.
    Returns a dict with the 13 features expected by the model.
    """
    return {
        "spf_pass": int(header_data.get("spf", "none") == "pass"),
        "dkim_pass": int(header_data.get("dkim", "none") == "pass"),
        "dmarc_aligned": int(header_data.get("dmarc", "none") == "pass"),
        "spf_result": header_data.get("spf", "none"),
        "dkim_result": header_data.get("dkim", "none"),
        "dmarc_result": header_data.get("dmarc", "none"),
        "reply_to_mismatch": int(bool(header_data.get("reply_to_mismatch", False))),
        "return_path_mismatch": int(bool(header_data.get("return_path_mismatch", False))),
        "sender_domain_age_days": geo_data.get("domain_age_days") or 9999,
        "num_urls": header_data.get("num_urls", 0),
        "url_domain_mismatch": header_data.get("url_domain_mismatch", 0),
        "urgency_word_count": header_data.get("urgency_word_count", 0),
        "has_attachment": header_data.get("has_attachment", 0),
        "sender_ip_is_vpn_hosting": int(bool(geo_data.get("is_vpn_or_hosting", False))),
        "subject_length": header_data.get("subject_length", 0),
        "body_length": header_data.get("body_length", 0),
        "suspicious_domain": bool(header_data.get("suspicious_domain", False)),
    }


def predict_fraud(features):
    """
    Predict fraud score (0-100) and triggered flags from a feature vector.
    Returns (score: int, flags: list[str]).
    """
    # The bundled model is trained on synthetic examples, so its raw output can
    # collapse to 0/99 on real mail. Use it as a weak prior and calibrate the
    # final score from observable forensic evidence instead.
    model_score = 50
    try:
        model = _load_model()
        df = pd.DataFrame([features])[FEATURE_COLUMNS]
        model_score = float(model.predict_proba(df)[0][1]) * 100
    except Exception:
        pass

    contributions = []
    def add(label, points, active):
        if active:
            contributions.append({"signal": label, "points": points})

    add("SPF failed", 14, features.get("spf_result") in ("fail", "softfail", "neutral"))
    add("DKIM failed", 12, features.get("dkim_result") == "fail")
    add("DMARC failed", 14, features.get("dmarc_result") == "fail")
    add("Reply-To mismatch", 18, features.get("reply_to_mismatch"))
    add("Return-Path mismatch", 7, features.get("return_path_mismatch"))
    add("Suspicious sender domain", 16, features.get("suspicious_domain"))
    add("URL domain mismatch", min(20, 10 + 4 * features.get("url_domain_mismatch", 0)), features.get("url_domain_mismatch", 0) > 0)
    add("Urgency / credential language", min(16, 4 + 3 * features.get("urgency_word_count", 0)), features.get("urgency_word_count", 0) >= 2)
    add("New sender domain", 12, features.get("sender_domain_age_days", 9999) < 90)
    add("Hosting or proxy sender IP", 10, features.get("sender_ip_is_vpn_hosting"))
    add("Unexpected attachment", 4, features.get("has_attachment"))

    evidence_score = min(100, sum(item["points"] for item in contributions))
    score = int(round(0.82 * evidence_score + 0.18 * model_score))
    if evidence_score >= 45:
        score = max(score, min(96, evidence_score + 10))
    score = max(1, min(99, score))

    # Determine which features triggered flags
    flag_features = [
        ("spf_result", "fail", "SPF failed"),
        ("dkim_result", "fail", "DKIM failed"),
        ("dmarc_result", "fail", "DMARC not aligned"),
        ("reply_to_mismatch", 1, "Reply-To mismatch"),
        ("return_path_mismatch", 1, "Return-Path mismatch"),
        ("sender_ip_is_vpn_hosting", 1, "Sender IP is VPN/hosting"),
        ("url_domain_mismatch", None, "URL domain mismatch"),
    ]

    flags = []
    for feat, trigger_val, label in flag_features:
        val = features.get(feat, 0)
        if trigger_val is None:
            # For numeric features, flag if > 0
            if val > 0:
                flags.append(label)
        elif val == trigger_val:
            flags.append(label)

    # Additional contextual flags
    if features.get("urgency_word_count", 0) >= 3:
        flags.append("High urgency language detected")

    domain_age = features.get("sender_domain_age_days", 9999)
    if domain_age < 30:
        flags.append(f"New domain ({domain_age} days old)")

    if features.get("num_urls", 0) > 5:
        flags.append(f"Excessive URLs ({features['num_urls']})")

    if features.get("suspicious_domain"):
        flags.append("Look-alike or high-risk sender domain")
    return score, flags, contributions


def get_risk_tier(fraud_score):
    """Classify fraud score into risk tiers."""
    if fraud_score >= 80:
        return "Critical"
    elif fraud_score >= 60:
        return "High"
    elif fraud_score >= 40:
        return "Medium"
    elif fraud_score >= 20:
        return "Low"
    else:
        return "Safe"
