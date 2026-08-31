# AI-Powered Email Threat Detection Platform — Implementation Plan

Build a full-stack forensic email analysis platform with Flask backend (6 modules) and React/Vite frontend, based on [plan.md](file:///c:/Users/akyas/Desktop/Desktop/sih/plan.md).

---

## Proposed Changes

### Phase 1: Backend Foundation

#### [NEW] `backend/requirements.txt`
All Python dependencies: Flask, flask-cors, xgboost, pandas, scikit-learn, google-generativeai, networkx, weasyprint, python-whois, dnspython, requests, mail-parser, jinja2, SQLAlchemy.

#### [NEW] `backend/db.py`
SQLite database layer using sqlite3. Cases table with: id, timestamp, fraud_score, risk_tier, flags, explanation, header_data, geo_data, evidence_hash, raw_eml_hash. CRUD operations for case management.

#### [NEW] `backend/parser.py` — Module 2: Header & Protocol Analysis
- Parse `.eml` files using Python `email` stdlib + `mail-parser`
- Extract SPF, DKIM, DMARC from `Authentication-Results` header
- Detect reply-to / return-path mismatches
- Count relay hops from `Received` headers
- Extract URLs from body, count urgency words, attachment detection
- Returns structured dict with all features needed by Module 1

#### [NEW] `backend/geo_intel.py` — Module 3: Origin Traceability
- Extract IPs from Received headers (earliest hop)
- Geolocation via `ip-api.com` (free, no key needed)
- WHOIS lookup via `python-whois` for domain age
- DNS checks via `dnspython`
- VPN/hosting provider detection via ip-api's `hosting` field
- Returns: IP, country, city, ISP, is_vpn_or_hosting, domain_age_days, lat/lon

#### [NEW] `backend/ml_model.py` — Module 1: XGBoost Fraud Detection
- 13-feature vector as specified in plan
- `build_feature_vector()` combining header + geo data
- `predict_fraud()` returns score (0–100) and triggered flags
- Loads pre-trained `fraud_model.json`

#### [NEW] `backend/train_model.py` — Offline Training Script
- Generates synthetic training data mimicking Nazario (malicious) + Enron (legitimate) distributions
- Trains XGBoost classifier (n_estimators=100, max_depth=4)
- Saves `fraud_model.json`
- Run once before demo

#### [NEW] `backend/explain.py` — Gemini Explanation Layer
- Uses `google-generativeai` SDK with user-provided API key
- Generates plain-English explanation from flags + score
- Graceful fallback when no API key provided
- Model: `gemini-2.0-flash` (stable)

#### [NEW] `backend/graph_correlate.py` — Module 4: Campaign Correlation
- NetworkX graph linking emails by shared IP, domain, registrar
- `add_email_to_graph()` and `find_campaign()` as specified
- Returns linked emails + confidence score
- Graph serialization for frontend visualization (nodes/edges JSON)

#### [NEW] `backend/privacy.py` — Module 6: Privacy & Compliance
- SHA-256 evidence hashing
- Email address PII masking (configurable)
- Retention policy config

#### [NEW] `backend/report_gen.py` — Module 5: PDF Report
- Jinja2 HTML template → WeasyPrint PDF
- 2-3 page forensic report with score, headers, trace, campaign, chain-of-custody
- SHA-256 evidence hash in footer

#### [NEW] `backend/app.py` — Flask Application
- Routes: `/api/analyze`, `/api/correlate`, `/api/report/<case_id>`, `/api/cases`, `/api/cases/<case_id>`
- CORS enabled
- Gemini key via `X-Gemini-Key` header
- File upload handling

#### [NEW] `backend/seed_data/email_001.eml` through `email_006.eml`
- 6 handcrafted `.eml` files as specified in plan Section 7
- Campaign A (001-003): shared IP `185.220.101.4`, NameCheap
- Campaign B (004): different actor
- Legitimate (005-006): Microsoft/AWS IPs

---

### Phase 2: Frontend (React + Vite + Tailwind)

#### [NEW] `frontend/` — Vite React project
Initialize with `npx create-vite` with React template.

#### [NEW] Frontend Components
| Component | Purpose |
|---|---|
| `ApiKeyInput.jsx` | Password-style Gemini key input → sessionStorage |
| `UploadPanel.jsx` | Drag-and-drop .eml upload with progress |
| `FraudScoreCard.jsx` | Animated gauge chart + risk tier badge |
| `HeaderTable.jsx` | SPF/DKIM/DMARC pass-fail table with icons |
| `TraceMap.jsx` | Leaflet map with IP geolocation pins |
| `CampaignGraph.jsx` | Force-directed graph (react-force-graph) |
| `ExplanationPanel.jsx` | AI-generated plain-English reasoning |
| `PrivacyToggle.jsx` | Toggle PII masking live |
| `CaseList.jsx` | Searchable case management table |
| `ExportButton.jsx` | Trigger PDF report download |
| `Dashboard.jsx` | Main layout assembling all components |
| `Navbar.jsx` | Top navigation bar |

#### Design System
- **Dark theme** with glassmorphism panels
- Color palette: Deep navy (`#0a0e27`), electric blue (`#00d4ff`), threat red (`#ff3366`), safe green (`#00ff88`)
- Font: Inter from Google Fonts
- Micro-animations: score counter animation, risk tier pulse, map pin drops
- Responsive grid layout

---

## Build Order

1. **Backend core** — `db.py`, `parser.py`, `geo_intel.py`, `privacy.py`
2. **ML pipeline** — `train_model.py`, `ml_model.py`, `explain.py`
3. **Campaign + Report** — `graph_correlate.py`, `report_gen.py`
4. **Flask app** — `app.py` wiring all modules
5. **Seed data** — 6 `.eml` files
6. **Frontend init** — Vite + React + Tailwind setup
7. **Frontend components** — All 12 components
8. **Integration test** — End-to-end with seed data

---

## Verification Plan

### Automated Tests
- `python backend/train_model.py` — verify model trains and saves
- `python backend/app.py` — verify Flask starts without errors
- `npm run dev` in frontend — verify React builds and renders
- Upload seed `.eml` files through the UI end-to-end

### Manual Verification
- Upload all 6 seed emails in sequence per demo script
- Verify campaign graph correctly clusters emails 001-003
- Verify emails 004, 005, 006 stay isolated
- Verify PDF report downloads with correct data
- Test with/without Gemini API key (fallback explanation)

> [!IMPORTANT]
> **WeasyPrint** requires system-level GTK/Cairo libraries on Windows. If installation fails, I'll fall back to a pure-HTML report with browser print-to-PDF, or use `fpdf2` as an alternative.

> [!IMPORTANT]
> **Training data**: Will use real Kaggle phishing email datasets. Primary: **"Phishing Email Dataset"** (~82,500 emails from Enron + Ling + CEAS + SpamAssassin with subject/body/labels). The `train_model.py` script will download the CSV, extract features from the raw text, and train XGBoost on real data. Requires a `kaggle.json` API key or manual CSV download to `backend/data/`.
