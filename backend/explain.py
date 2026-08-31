"""
Gemini Explanation Layer
Generates plain-English explanations of fraud analysis results.
Gemini is used ONLY for explanation — never for classification.
XGBoost owns the fraud/not-fraud decision.
"""

from google import genai
from google.genai import types

# gemini-2.0-flash is deprecated and returns 404 for new API keys
MODEL_CANDIDATES = (
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
)

_GENERATE_CONFIG = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def get_explanation(flags, fraud_score, gemini_key=None):
    """
    Generate a plain-English explanation for the fraud analysis.
    If no Gemini API key is provided, returns a template-based fallback.
    """
    if not gemini_key:
        return _fallback_explanation(flags, fraud_score)

    try:
        client = genai.Client(api_key=gemini_key)

        risk_tier = _get_risk_word(fraud_score)
        flags_text = ", ".join(flags) if flags else "no specific red flags"

        prompt = f"""You are a cybersecurity analyst writing a brief forensic summary.
An email was analyzed and received a fraud score of {fraud_score}/100 ({risk_tier} risk).
Detected signals: {flags_text}.

Write a 2-3 sentence plain-English explanation for a security investigator,
describing why this email was assessed at this risk level based on the detected signals.
Be specific, professional, and actionable. Do not use markdown formatting."""

        text = _call_gemini(client, prompt)
        if text:
            return text
        return _fallback_explanation(flags, fraud_score)

    except Exception:
        return _fallback_explanation(flags, fraud_score)


def _call_gemini(client, prompt):
    """Try current Gemini models until one succeeds."""
    last_error = None

    for model in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=_GENERATE_CONFIG,
            )
            if response.text:
                return response.text.strip()
        except Exception as exc:
            last_error = exc
            err = str(exc)
            if "404" in err or "NOT_FOUND" in err:
                continue
            raise

    if last_error:
        raise last_error
    return None


def _fallback_explanation(flags, fraud_score):
    """Template-based explanation when Gemini is not available."""
    risk = _get_risk_word(fraud_score)

    if not flags:
        return (
            f"This email received a fraud score of {fraud_score}/100, "
            f"classified as {risk} risk. No specific red flags were detected."
        )

    flags_text = ", ".join(flags[:5])
    return (
        f"This email received a fraud score of {fraud_score}/100, "
        f"classified as {risk} risk. "
        f"The following signals contributed to this assessment: {flags_text}."
    )


def _get_risk_word(score):
    if score >= 80:
        return "critical"
    elif score >= 60:
        return "high"
    elif score >= 40:
        return "medium"
    elif score >= 20:
        return "low"
    return "minimal"
