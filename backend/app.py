"""
Flask Application — API Entrypoint
Wires all modules together into REST API endpoints.
"""

import os
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from parser import parse_eml
from geo_intel import trace_origin
from ml_model import build_feature_vector, predict_fraud, get_risk_tier
from explain import get_explanation
from graph_correlate import add_email_to_graph, find_campaign, get_graph_data, clear_graph
from privacy import compute_evidence_hash, mask_result
from report_gen import generate_report
from db import save_case, get_case, get_all_cases, delete_case

app = Flask(__name__)
CORS(app)


@app.route("/api/analyze", methods=["POST"])
def analyze_email():
    """
    Main analysis endpoint. Accepts a .eml file upload.
    Runs the full pipeline: parse → geo → ML → explain → correlate → store.
    """
    if "email_file" not in request.files:
        return jsonify({"error": "No email_file provided"}), 400

    eml_file = request.files["email_file"]
    gemini_key = request.headers.get("X-Gemini-Key", "")
    filename = eml_file.filename or "unknown.eml"

    # Read the raw bytes
    eml_bytes = eml_file.read()

    # Module 6: Evidence hash
    evidence_hash = compute_evidence_hash(eml_bytes)

    # Module 2: Header parsing
    header_data = parse_eml(eml_bytes)

    # Module 3: Geolocation & WHOIS
    geo_data = trace_origin(
        header_data.get("relay_hops", []),
        from_domain=header_data.get("from_domain")
    )

    # Module 1: ML prediction
    features = build_feature_vector(header_data, geo_data)
    try:
        fraud_score, flags, contributions = predict_fraud(features)
    except Exception:
        # Model not trained yet — use heuristic scoring
        fraud_score = _heuristic_score(features)
        flags = _heuristic_flags(features)
        contributions = []

    risk_tier = get_risk_tier(fraud_score)

    # Gemini explanation
    explanation = get_explanation(flags, fraud_score, gemini_key)

    # Build result
    result = {
        "fraud_score": fraud_score,
        "risk_tier": risk_tier,
        "flags": flags,
        "risk_contributions": contributions,
        "llm_explanation": explanation,
        "header_analysis": header_data,
        "geo_trace": geo_data,
        "evidence_hash": evidence_hash,
        "raw_eml_hash": evidence_hash,
    }

    # Module 4: Campaign correlation
    case_id = save_case(result, filename=filename)
    result["case_id"] = case_id

    graph_data = add_email_to_graph(case_id, header_data, geo_data)
    campaign = find_campaign(case_id)
    result["campaign_data"] = campaign
    result["graph_data"] = graph_data

    return jsonify(result)


@app.route("/api/correlate", methods=["POST"])
def correlate_campaign():
    """Find campaign links for a given email case."""
    data = request.get_json()
    if not data or "email_id" not in data:
        return jsonify({"error": "email_id required"}), 400

    campaign = find_campaign(data["email_id"])
    return jsonify(campaign)


@app.route("/api/graph", methods=["GET"])
def get_full_graph():
    """Return the full campaign correlation graph."""
    return jsonify(get_graph_data())


@app.route("/api/graph/clear", methods=["POST"])
def clear_campaign_graph():
    """Clear the campaign correlation graph."""
    return jsonify(clear_graph())


@app.route("/api/report/<case_id>", methods=["GET"])
def export_report(case_id):
    """Generate and download a forensic PDF report for a case."""
    case = get_case(case_id)
    if case is None:
        return jsonify({"error": "Case not found"}), 404

    # Add campaign data
    campaign = find_campaign(case_id)
    case["campaign_data"] = campaign
    case["case_id"] = case_id

    # Apply privacy masking
    mask = request.args.get("mask", "false").lower() == "true"
    if mask:
        case = mask_result(case, mask=True)

    try:
        pdf_path = generate_report(case)
    except Exception as exc:
        return jsonify({"error": f"Report generation failed: {exc}"}), 500

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"forensic_report_{case_id}.pdf",
        mimetype="application/pdf"
    )


@app.route("/api/cases", methods=["GET"])
def list_cases():
    """List all stored cases."""
    cases = get_all_cases()
    # Return a summary view (without full header/geo data)
    summaries = []
    for c in cases:
        summaries.append({
            "id": c["id"],
            "created_at": c["created_at"],
            "filename": c["filename"],
            "fraud_score": c["fraud_score"],
            "risk_tier": c["risk_tier"],
            "flags": c.get("flags", []),
            "evidence_hash": c.get("evidence_hash"),
        })
    return jsonify(summaries)


@app.route("/api/analytics", methods=["GET"])
def analytics():
    """Aggregated, privacy-safe data for the dashboard visualisations."""
    cases = get_all_cases()
    tiers = ["Safe", "Low", "Medium", "High", "Critical"]
    tier_distribution = {tier: 0 for tier in tiers}
    score_distribution = [0] * 10
    top_senders, countries, domain_age_points, daily, words = {}, {}, [], {}, {}
    for case in cases:
        score = max(0, min(99, int(case.get("fraud_score") or 0)))
        score_distribution[min(9, score // 10)] += 1
        tier = case.get("risk_tier", "Safe")
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        header, geo = case.get("header_analysis") or {}, case.get("geo_trace") or {}
        domain = header.get("from_domain") or "unknown"
        top_senders[domain] = top_senders.get(domain, 0) + 1
        if geo.get("country"):
            countries[geo["country"]] = countries.get(geo["country"], 0) + 1
        if geo.get("domain_age_days") is not None:
            domain_age_points.append({"age": geo["domain_age_days"], "score": score})
        day = (case.get("created_at") or "")[:10]
        if day:
            daily.setdefault(day, {t: 0 for t in tiers})[tier] += 1
        if tier in ("High", "Critical"):
            for word in re.findall(r"[a-z]{4,}", (header.get("subject") or "").lower()):
                if word not in {"your", "with", "from", "that", "this", "have", "will"}:
                    words[word] = words.get(word, 0) + 1
    return jsonify({
        "tier_distribution": tier_distribution,
        "score_distribution": score_distribution,
        "top_senders": sorted(top_senders.items(), key=lambda x: x[1], reverse=True)[:8],
        "countries": countries,
        "domain_age_points": domain_age_points[-100:],
        "daily": [{"date": date, **values} for date, values in sorted(daily.items())[-30:]],
        "word_cloud": sorted(words.items(), key=lambda x: x[1], reverse=True)[:24],
        "total_cases": len(cases),
    })


@app.route("/api/cases/<case_id>", methods=["GET"])
def get_case_detail(case_id):
    """Get full details for a specific case."""
    case = get_case(case_id)
    if case is None:
        return jsonify({"error": "Case not found"}), 404

    # Check for PII masking
    mask = request.args.get("mask", "false").lower() == "true"
    if mask:
        case = mask_result(case, mask=True)

    # Add campaign data
    campaign = find_campaign(case_id)
    case["campaign_data"] = campaign

    return jsonify(case)


@app.route("/api/cases/<case_id>", methods=["DELETE"])
def remove_case(case_id):
    """Delete a case."""
    delete_case(case_id)
    return jsonify({"status": "deleted", "case_id": case_id})


def _heuristic_score(features):
    """Fallback scoring when ML model is not available."""
    score = 30  # base
    if not features.get("spf_pass"):
        score += 15
    if not features.get("dkim_pass"):
        score += 10
    if not features.get("dmarc_aligned"):
        score += 10
    if features.get("reply_to_mismatch"):
        score += 10
    if features.get("return_path_mismatch"):
        score += 5
    if features.get("sender_ip_is_vpn_hosting"):
        score += 10
    if features.get("urgency_word_count", 0) >= 3:
        score += 5
    if features.get("url_domain_mismatch", 0) > 0:
        score += 5
    domain_age = features.get("sender_domain_age_days", 9999)
    if domain_age < 30:
        score += 10
    return min(score, 100)


def _heuristic_flags(features):
    """Fallback flag detection when ML model is not available."""
    flags = []
    if not features.get("spf_pass"):
        flags.append("SPF failed")
    if not features.get("dkim_pass"):
        flags.append("DKIM failed")
    if not features.get("dmarc_aligned"):
        flags.append("DMARC not aligned")
    if features.get("reply_to_mismatch"):
        flags.append("Reply-To mismatch")
    if features.get("return_path_mismatch"):
        flags.append("Return-Path mismatch")
    if features.get("sender_ip_is_vpn_hosting"):
        flags.append("Sender IP is VPN/hosting")
    if features.get("urgency_word_count", 0) >= 3:
        flags.append("High urgency language detected")
    return flags


if __name__ == "__main__":
    app.run(debug=True, port=5000)
