
# AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform

**Problem Statement ID: 26106**

---

## 1. Overview

Current email security tools primarily focus on filtering or blocking suspicious emails. However, organizations lack the ability to deeply investigate the origin of fraudulent emails, trace their path, and build forensic evidence.

This platform solves that gap by combining:

- AI-powered fraud detection
- Deep email header forensics
- IP geolocation and origin tracing
- Graph-based campaign attribution
- Auto-generated forensic reports with chain-of-custody

It is designed as an **investigator’s cockpit** for SOC teams, institutional admins, fraud units, and law enforcement.

---

## 2. Key Features

- Real-time fraud risk scoring (0–100)
- SPF, DKIM, and DMARC validation
- Hop-by-hop geolocation trace map
- VPN / Hosting provider detection
- Campaign correlation using shared infrastructure
- Plain-English AI explanation of findings
- One-click forensic PDF report
- SHA-256 evidence hash for chain-of-custody
- PII masking and privacy controls
- Case management view

---

## 3. Tech Stack

### Backend
- Flask (Python) – REST API
- flask-cors
- email + mail-parser – .eml parsing
- XGBoost – Fraud classification
- google-generativeai – Gemini explanation layer
- NetworkX – Campaign graph correlation
- WeasyPrint – PDF report generation
- python-whois, dnspython – Domain intelligence
- requests – IP geolocation (ip-api.com)
- SQLite – Case storage

### Frontend
- React (Vite)
- Tailwind CSS
- Recharts – Charts
- Leaflet.js – Geolocation trace map
- vis.js / react-force-graph – Campaign graph

### Datasets
- Nazario Phishing Corpus
- Enron Email Dataset
- 6 handcrafted seed `.eml` files for reliable testing

---

## 4. System Architecture

```text
.eml Upload
    ↓
Module 2: Header Parsing (SPF / DKIM / DMARC)
    ↓
Module 3: Geolocation + WHOIS
    ↓
Module 1: XGBoost Fraud Score + Gemini Explanation
    ↓
Module 4: NetworkX Campaign Correlation
    ↓
Module 6: Privacy (PII Masking + SHA-256 Hash)
    ↓
Module 5: Dashboard + Forensic PDF Report
```

---

## 5. Modules

| # | Module                              | Technology          | Uses ML? |
|---|-------------------------------------|---------------------|----------|
| 1 | Fraud Detection Engine              | XGBoost + Gemini    | Yes      |
| 2 | Header & Protocol Analysis          | Regex / Parsing     | No       |
| 3 | Origin Traceability & Geolocation   | ip-api + WHOIS      | No       |
| 4 | Identity Correlation & Attribution  | NetworkX            | No       |
| 5 | Dashboard & Forensic Reporting      | React + WeasyPrint  | No       |
| 6 | Privacy, Legal & Compliance         | SHA-256 + Masking   | No       |

**Important:** Only Module 1 uses Machine Learning. Gemini is used only for generating plain-English explanations, not for making the fraud decision.

---

## 6. Project Structure

```text
project-root/
├── backend/
│   ├── app.py
│   ├── parser.py              # Module 2
│   ├── geo_intel.py           # Module 3
│   ├── ml_model.py            # Module 1
│   ├── train_model.py
│   ├── explain.py             # Gemini explanation
│   ├── graph_correlate.py     # Module 4
│   ├── privacy.py             # Module 6
│   ├── report_gen.py          # Module 5
│   ├── db.py
│   ├── requirements.txt
│   └── seed_data/
│       ├── email_001.eml
│       ├── email_002.eml
│       ├── email_003.eml
│       ├── email_004.eml
│       ├── email_005.eml
│       └── email_006.eml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadPanel.jsx
│   │   │   ├── FraudScoreCard.jsx
│   │   │   ├── HeaderTable.jsx
│   │   │   ├── TraceMap.jsx
│   │   │   ├── CampaignGraph.jsx
│   │   │   ├── ExplanationPanel.jsx
│   │   │   ├── PrivacyToggle.jsx
│   │   │   ├── CaseList.jsx
│   │   │   └── ExportButton.jsx
│   │   └── ...
│   └── package.json
└── README.md
```

---

## 7. How to Run

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py
```

Backend will run on: `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on: `http://localhost:5173`

---

## 8. API Endpoints

| Method | Endpoint                  | Description                     |
|--------|---------------------------|---------------------------------|
| POST   | `/api/analyze`            | Analyze uploaded .eml file      |
| POST   | `/api/correlate`          | Get campaign correlation        |
| GET    | `/api/report/<case_id>`   | Download forensic PDF report    |
| GET    | `/api/cases`              | List all analyzed cases         |

---

## 9. Demo Flow

1. Enter Gemini API Key
2. Upload `email_001.eml` → High fraud score + Trace Map
3. Upload `email_002.eml` and `email_003.eml` → Campaign graph appears
4. Upload legitimate email → Low score, stays isolated
5. Click **Export Report** → Download forensic PDF with SHA-256 hash

---

## 10. Key Design Decisions

- **XGBoost** makes the actual fraud decision (deterministic and auditable)
- **Gemini** only explains the result in plain English
- VPN/Hosting IPs are explicitly flagged instead of giving false precision
- Human-in-the-loop design (no automatic blocking)
- SHA-256 hash included in every report for chain-of-custody
- Modular architecture — easy to extend

---

## 11. Future Scope

- Integration with Google Workspace / Microsoft 365
- Real-time IMAP monitoring
- Multi-tenant support for institutions
- Advanced threat intelligence feeds
- Mobile-responsive analyst view

---

## License

This project is open for educational and research purposes.
```
