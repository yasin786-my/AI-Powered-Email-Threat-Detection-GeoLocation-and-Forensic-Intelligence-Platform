# 🕵️ PS 26106 — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform
## Full Implementation Plan

---

## 1. Tech Stack (Final)

### Backend
- **Flask** (Python) — REST API
- `flask-cors` — allow React frontend to call Flask API
- **email** (stdlib) + **mail-parser** — .eml parsing
- **XGBoost** — fraud classification model (Module 1)
- **google-generativeai** SDK — Gemini API for explanation text (`gemini-3-flash-preview`)
- **NetworkX** — campaign correlation graph (Module 4)
- **WeasyPrint** — HTML → PDF forensic report (Module 5)
- **python-whois**, **dnspython** — domain intelligence (Module 3)
- **requests** — IP geolocation via ip-api.com (Module 3)
- **SQLite** (`sqlite3` / `SQLAlchemy`) — case storage

### Frontend
- **React** (Vite)
- **Tailwind CSS**
- **Recharts** — fraud score / flag charts
- **Leaflet.js** — geolocation trace map
- **vis.js** / **react-force-graph** — campaign graph
- API key input field (password-style) for Gemini key — stored in `sessionStorage`, sent per-request as a header

### Datasets
- **Nazario Phishing Corpus** — malicious training/test samples
- **Enron Dataset** — legitimate baseline samples
- **Handcrafted seed `.eml` set** (6 files) — guaranteed demo-safe Module 4 correlation

---

## 2. Module-by-Module Build Plan

| # | Module | Core logic | Uses ML? | Dataset needed? |
|---|---|---|---|---|
| 1 | Fraudulent Email Detection Engine | XGBoost trained on engineered features + Gemini for explanation text | ✅ XGBoost | ✅ Nazario + Enron |
| 2 | Email Header & Protocol Analysis | Regex parsing of `.eml` headers + `Authentication-Results` | ❌ | ❌ |
| 3 | Origin Traceability & Location Analysis | IP extraction, ip-api.com, WHOIS, DNS | ❌ | ❌ |
| 4 | Identity Correlation & Attribution | NetworkX graph on shared IP/domain/registrar | ❌ | ❌ (seed data only) |
| 5 | Alerting, Dashboard & Forensic Reporting | React dashboard + WeasyPrint PDF export | ❌ | ❌ |
| 6 | Privacy, Legal & Compliance Safeguards | PII masking, SHA-256 evidence hash, retention config | ❌ | ❌ |

**Key architectural rule:** Only Module 1 does actual machine learning. Modules 2, 3, 4 are deterministic engineering that *feed features into* Module 1. Module 5 is the presentation layer. Module 6 is policy/design. This separation is your strongest answer if a judge asks "where's the AI in your AI platform."

---

## 3. Data Flow (End to End)

```
.eml upload
    │
    ▼
Module 2: Header parsing → {spf, dkim, dmarc, reply_to_mismatch, relay_hops}
    │
    ▼
Module 3: Geolocation + WHOIS → {earliest_hop_ip, country, city, is_vpn, domain_age_days}
    │
    ▼
Module 1: XGBoost → fraud_score (0-100)
    │
    ▼
Gemini API call → llm_explanation (plain-English reasoning)
    │
    ▼
Module 4: NetworkX → campaign correlation (if multiple emails uploaded)
    │
    ▼
Module 6: PII masking + SHA-256 evidence hash applied
    │
    ▼
Module 5: Unified JSON → Dashboard (live) + WeasyPrint → Forensic PDF
```

---

## 4. Flask Backend — API Structure

```
backend/
├── app.py                   # Flask app entrypoint, routes
├── parser.py                 # Module 2: .eml parsing, header extraction
├── geo_intel.py               # Module 3: IP geolocation, WHOIS, DNS
├── ml_model.py                # Module 1: XGBoost load/predict
├── train_model.py             # One-time offline script: trains XGBoost on Nazario+Enron
├── explain.py                  # Module 1: Gemini API call for explanation
├── graph_correlate.py          # Module 4: NetworkX campaign linking
├── privacy.py                   # Module 6: masking, hashing, retention
├── report_gen.py                 # Module 5: WeasyPrint PDF generation
├── db.py                          # SQLite case storage
├── requirements.txt
└── seed_data/
    ├── email_001.eml ... email_006.eml   # Module 4 demo set
```

### Core Flask routes

```python
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/analyze", methods=["POST"])
def analyze_email():
    eml_file = request.files["email_file"]
    gemini_key = request.headers.get("X-Gemini-Key")

    header_data = parse_headers(eml_file)          # Module 2
    geo_data = trace_origin(header_data["relay_hops"])  # Module 3
    features = build_feature_vector(header_data, geo_data)
    fraud_score, flags = predict_fraud(features)     # Module 1 (XGBoost)
    explanation = get_explanation(flags, fraud_score, gemini_key)  # Gemini

    result = {
        "fraud_score": fraud_score,
        "risk_tier": get_risk_tier(fraud_score),
        "flags": flags,
        "llm_explanation": explanation,
        "header_analysis": header_data,
        "geo_trace": geo_data
    }
    save_case(result)   # SQLite
    return jsonify(result)


@app.route("/api/correlate", methods=["POST"])
def correlate_campaign():
    email_id = request.json["email_id"]
    campaign = find_campaign(email_id)   # Module 4
    return jsonify(campaign)


@app.route("/api/report/<case_id>", methods=["GET"])
def export_report(case_id):
    pdf_path = generate_report(case_id)  # Module 5 + Module 6 hash/mask
    return send_file(pdf_path, as_attachment=True)


@app.route("/api/cases", methods=["GET"])
def list_cases():
    return jsonify(get_all_cases())   # for dashboard case management view


if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

---

## 5. Module 1 — XGBoost Feature Engineering

```python
FEATURE_COLUMNS = [
    "spf_pass", "dkim_pass", "dmarc_aligned",
    "reply_to_mismatch", "return_path_mismatch",
    "sender_domain_age_days", "num_urls", "url_domain_mismatch",
    "urgency_word_count", "has_attachment",
    "sender_ip_is_vpn_hosting", "subject_length", "body_length"
]

def build_feature_vector(header_data, geo_data):
    return {
        "spf_pass": int(header_data["spf"] == "pass"),
        "dkim_pass": int(header_data["dkim"] == "pass"),
        "dmarc_aligned": int(header_data["dmarc"] == "pass"),
        "reply_to_mismatch": int(header_data["reply_to_mismatch"]),
        "return_path_mismatch": int(header_data["return_path_mismatch"]),
        "sender_domain_age_days": geo_data.get("domain_age_days") or 9999,
        "num_urls": header_data.get("num_urls", 0),
        "url_domain_mismatch": header_data.get("url_domain_mismatch", 0),
        "urgency_word_count": header_data.get("urgency_word_count", 0),
        "has_attachment": header_data.get("has_attachment", 0),
        "sender_ip_is_vpn_hosting": int(geo_data.get("is_vpn_or_hosting", False)),
        "subject_length": header_data.get("subject_length", 0),
        "body_length": header_data.get("body_length", 0)
    }
```

**Training (offline, one-time, run before the hackathon demo):**
```python
import xgboost as xgb
import pandas as pd

# X = feature dataframe built from Nazario (label=1) + Enron (label=0) samples
model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1)
model.fit(X_train, y_train)
model.save_model("fraud_model.json")
```

**Inference (in Flask):**
```python
model = xgb.XGBClassifier()
model.load_model("fraud_model.json")

def predict_fraud(features):
    df = pd.DataFrame([features])[FEATURE_COLUMNS]
    score = int(model.predict_proba(df)[0][1] * 100)
    flags = [k for k, v in features.items() if v in (1, True) and k not in ["subject_length", "body_length"]]
    return score, flags
```

---

## 6. Gemini Explanation Layer (Explanation only, not classification)

```python
import google.generativeai as genai

def get_explanation(flags, fraud_score, gemini_key):
    if not gemini_key:
        return f"This email was flagged due to: {', '.join(flags)}."  # fallback, no API needed

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-3-flash-preview")
    prompt = f"""
    An email was flagged with fraud score {fraud_score}/100.
    Detected signals: {', '.join(flags)}.
    Write a 2-3 sentence plain-English explanation for a security analyst,
    describing why this email is likely fraudulent based on these signals.
    """
    response = model.generate_content(prompt)
    return response.text
```

**Key architectural rule:** Gemini never decides fraud/not-fraud — XGBoost owns that decision. Gemini only writes the human-readable explanation. This keeps the security decision deterministic and auditable.

---

## 7. Module 4 — Seed Data & Demo

### Seed set design (6 handcrafted `.eml` files)

| File | Sender domain | Sender IP | Registrar | Role in demo |
|---|---|---|---|---|
| `email_001.eml` | paypa1-support.com | 185.220.101.4 | NameCheap | Campaign A — fraud |
| `email_002.eml` | paypa1-support.com | 185.220.101.4 | NameCheap | Campaign A — fraud (same infra) |
| `email_003.eml` | paypal-billing-secure.net | 185.220.101.4 | NameCheap | Campaign A — fraud (diff domain, same IP) |
| `email_004.eml` | urgent-invoice-corp.com | 91.203.5.12 | Porkbun | Campaign B — fraud (unrelated actor) |
| `email_005.eml` | hr@yourcompany.com | 40.92.20.10 (Microsoft) | — | Legitimate — no correlation |
| `email_006.eml` | newsletter@retailer.com | 52.10.30.5 (AWS, legit bulk sender) | — | Legitimate — no correlation |

### Demo script
1. Upload `email_001.eml` → analyzed, flagged high risk, no campaign yet (first sighting)
2. Upload `email_002.eml` and `email_003.eml` → system detects shared IP `185.220.101.4` → **campaign graph appears live**, 3 emails clustered
3. Upload `email_004.eml` → flagged high risk but **stays isolated** (different infrastructure) → shows the system doesn't over-correlate
4. Upload `email_005.eml` / `email_006.eml` → low risk, no flags, clearly separate from the fraud cluster

This sequence proves both *precision* (doesn't merge unrelated fraud) and *recall* (correctly links shared infrastructure) in about 90 seconds on stage.

### Graph correlation code (Module 4, recap)
```python
import networkx as nx

G = nx.Graph()

def add_email_to_graph(email_id, header_data, geo_data):
    G.add_node(email_id, type="email")
    ip = geo_data.get("earliest_hop_ip")
    domain = header_data.get("from_domain")
    if ip:
        G.add_node(ip, type="ip")
        G.add_edge(email_id, ip)
    if domain:
        G.add_node(domain, type="domain")
        G.add_edge(email_id, domain)

def find_campaign(email_id):
    if email_id not in G:
        return {"linked_emails": [], "confidence": 0}
    connected = nx.node_connected_component(G, email_id)
    linked = [n for n in connected if G.nodes[n]["type"] == "email" and n != email_id]
    confidence = min(len(linked) * 25 + 25, 100) if linked else 0
    return {"linked_emails": linked, "confidence": confidence}
```

---

## 8. Module 6 — Privacy Layer (recap, quick to build)

```python
import hashlib

def compute_evidence_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def mask_email(email_address, mask=True):
    if not mask:
        return email_address
    name, domain = email_address.split("@")
    masked = name[0] + "***" + name[-1] if len(name) > 2 else "***"
    return f"{masked}@{domain}"
```
Include the hash + masking toggle state in every report footer.

---

## 9. Forensic PDF Report (WeasyPrint)

```python
from weasyprint import HTML
from jinja2 import Template

REPORT_TEMPLATE = Template("""
<html><body style="font-family:sans-serif">
<h1>Forensic Analysis Report — {{ case_id }}</h1>
<p>Generated: {{ timestamp }}</p>
<h2>Fraud Assessment</h2>
<p><b>Score:</b> {{ fraud_score }}/100 ({{ risk_tier }})</p>
<p>{{ llm_explanation }}</p>
<h2>Header Analysis</h2>
<table border="1" cellpadding="6">
  <tr><th>SPF</th><td>{{ spf }}</td></tr>
  <tr><th>DKIM</th><td>{{ dkim }}</td></tr>
  <tr><th>DMARC</th><td>{{ dmarc }}</td></tr>
</table>
<h2>Origin Trace</h2>
<p>{{ earliest_hop_ip }} — {{ city }}, {{ country }} ({{ isp }})</p>
<h2>Campaign Correlation</h2>
<p>{{ campaign_summary }}</p>
<h2>Chain of Custody</h2>
<p>Report ID: {{ report_id }} | Evidence hash (SHA-256): {{ evidence_hash }}</p>
</body></html>
""")

def generate_report(data):
    html = REPORT_TEMPLATE.render(**data)
    path = f"report_{data['case_id']}.pdf"
    HTML(string=html).write_pdf(path)
    return path
```

**Page structure (2-3 pages):**
- Page 1: Executive summary — fraud score, LLM explanation, key flags
- Page 2: Header forensics table + origin trace
- Page 3: Campaign correlation + chain-of-custody footer (only if campaign data exists)

---

## 10. Frontend — Dashboard Component Map

| Component | Data source | Notes |
|---|---|---|
| `ApiKeyInput.jsx` | User input | Password-style Gemini key field, `sessionStorage` |
| `UploadPanel.jsx` | User input | Drag-and-drop `.eml` upload |
| `FraudScoreCard.jsx` | Module 1 | Gauge chart, risk tier badge |
| `HeaderTable.jsx` | Module 2 | SPF/DKIM/DMARC pass-fail table |
| `TraceMap.jsx` | Module 3 | Leaflet map, VPN/hosting badge |
| `CampaignGraph.jsx` | Module 4 | vis.js node graph |
| `ExplanationPanel.jsx` | Gemini | Plain-English reasoning |
| `PrivacyToggle.jsx` | Module 6 | Mask/unmask PII live |
| `CaseList.jsx` | SQLite | Searchable case management table |
| `ExportButton.jsx` | Module 5 | Triggers `/api/report/<case_id>` download |

---

## 11. Build Order (24-36hr Hackathon Timeline)

| Phase | Hours | Tasks |
|---|---|---|
| 0. Research | 0–4 | Read SPF/DKIM/DMARC, collect Nazario/Enron samples, handcraft 6 seed `.eml` files |
| 1. Backend core | 4–10 | Flask app skeleton, Module 2 (header parsing), Module 3 (geolocation/WHOIS) |
| 2. ML pipeline | 10–16 | Train XGBoost offline, wire `/api/analyze`, integrate Gemini explanation call |
| 3. Frontend core | 16–22 | Upload panel, fraud score card, header table, trace map |
| 4. Module 4 + 5 | 22–28 | Campaign graph, PDF report generation, case list view |
| 5. Module 6 + polish | 28–32 | Privacy toggle, evidence hash, PDF footer, UI polish |
| 6. Rehearsal | 32–36 | Run the 6-email seed demo end-to-end 3+ times, prep Q&A answers |

---

## 12. Demo Script (5 minutes)

1. Enter Gemini API key in the password field (10 sec)
2. Upload `email_001.eml` → dashboard populates: fraud score 87, SPF/DKIM/DMARC fail table, trace map pins Amsterdam (flagged as hosting provider) (60 sec)
3. Point out the Gemini-generated plain-English explanation (20 sec)
4. Upload `email_002.eml` and `email_003.eml` → campaign graph appears live, 3 emails linked by shared IP (60 sec)
5. Upload `email_005.eml` (legitimate) → low score, stays isolated, proves no false clustering (30 sec)
6. Click "Export Report" → show PDF with score, headers, trace, campaign, and SHA-256 evidence hash (40 sec)
7. Close with the one-line differentiator: *"No existing tool combines detection, forensic headers, geolocation, and campaign attribution into one investigator-facing platform — that gap is what we built."* (20 sec)

---

## 13. Final Verdict Recap

**🟢 Green Light** — All 6 modules are scoped to hackathon-realistic builds: 1 real ML model (XGBoost) fused with deterministic forensics (Modules 2, 3, 4), a working dashboard + PDF report (Module 5), and lightweight-but-genuine privacy safeguards (Module 6). The seed data set guarantees a reliable, repeatable live demo regardless of network conditions, with Gemini's free API adding a strong explainability layer without locking the team into a fixed backend key.