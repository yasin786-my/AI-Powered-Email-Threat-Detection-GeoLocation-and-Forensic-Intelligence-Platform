# 26106 - AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform

CyberForensix analyzes `.eml` files for phishing and fraud indicators. It combines email-header authentication, sender-domain checks, original public-relay attribution, explainable risk scoring, campaign correlation, analytics, and downloadable forensic PDF reports.

## Features

- Upload and inspect `.eml` messages.
- Check SPF, DKIM, DMARC, Reply-To, Return-Path, URLs, urgency language, attachments, and suspicious sender domains.
- Identify the oldest public IP from `Received` headers and enrich it with IP geolocation, hosting/VPN context, domain age, RDAP/WHOIS, and a relay path.
- Produce an explainable fraud score from 0 to 100 with signal-by-signal contributions.
- Browse case history, correlations, analytics, and export an evidence-focused PDF report.

## Risk levels

| Fraud score | Classification |
| --- | --- |
| 0-19 | Safe |
| 20-39 | Low risk |
| 40-59 | Medium risk |
| 60-79 | High risk |
| 80-100 | Critical risk |

The map identifies the original **public relay** from the current email's headers. It is network attribution, not proof of the sender's exact physical location.

## Explainable scoring signals

Scores are calibrated from observable evidence. The model output is used as a weak prior, while the following signals provide the analyst-visible contribution.

| Signal | Score impact |
| --- | --- |
| SPF is missing, failed, soft-failed, or neutral | +18 |
| DKIM is missing, failed, soft-failed, or neutral | +16 |
| DMARC is missing, failed, soft-failed, or neutral | +18 |
| Original public relay IP is VPN/hosting | +22 |
| Reply-To address differs from sender | +12 |
| Return-Path differs from sender | +7 |
| Suspicious/look-alike sender domain | +16 |
| URL-domain mismatch | +10 to +20 |
| Urgency or credential language | +4 to +16 |
| Newly registered sender domain | +12 |
| Unexpected attachment | +4 |

## Run locally

### Backend

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API starts at `http://localhost:5000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

## Optional enrichment

IP geolocation uses `ip-api.com`; reverse locality uses OpenStreetMap Nominatim; domain age uses RDAP with WHOIS fallback. These are best-effort enrichments and can be disabled using these environment variables:

```text
ENABLE_NETWORK_ENRICHMENT=0
ENABLE_DOMAIN_AGE_ENRICHMENT=0
ENABLE_WHOIS_ENRICHMENT=0
```

For Gemini-powered analyst explanations, paste a Gemini API key into the dashboard. The key stays in browser session storage and is sent only with the analysis request.

## Project structure

```text
backend/   Flask API, parsing, scoring, geolocation, database, PDF generation
frontend/  React + Vite investigation dashboard
```
