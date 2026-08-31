"""
Module 5: Forensic PDF Report Generation
Uses fpdf2 to generate professional forensic analysis reports.
(fpdf2 chosen over WeasyPrint to avoid GTK/Cairo system dependencies on Windows)
"""

import os
import uuid
from datetime import datetime, timezone
from fpdf import FPDF


REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

_UNICODE_REPLACEMENTS = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2026": "...",
    "\u2022": "*",
    "\u25cf": "*",
    "\u00a0": " ",
}


def _pdf_text(value):
    """Normalize text for core Helvetica fonts (latin-1 only)."""
    if value is None:
        return "N/A"
    text = str(value)
    for src, dst in _UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ForensicReport(FPDF):
    """Custom FPDF class for forensic analysis reports."""

    def header(self):
        self.set_fill_color(26, 26, 26)
        self.rect(0, 0, 210, 18, style="F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(232, 232, 232)
        self.set_xy(12, 5)
        self.cell(0, 7, "26106 - AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(154, 154, 154)
        self.set_xy(12, 12)
        self.cell(0, 4, "Forensic email analysis report", align="L")
        self.set_y(25)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(47, 47, 47)
        self.line(12, self.get_y(), 198, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.set_text_color(102, 102, 102)
        self.cell(0, 8, f"CONFIDENTIAL  |  Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.ln(3)
        self.set_fill_color(224, 108, 117)
        self.rect(12, self.get_y() + 2, 3, 7, style="F")
        self.set_x(19)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(35, 35, 35)
        self.cell(0, 10, _pdf_text(title))
        # The title cell itself does not advance the cursor. Move below its
        # full height so subsequent paragraphs never overlap the heading.
        self.ln(12)

    def key_value(self, key, value, bold_value=False):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(60, 7, f"{_pdf_text(key)}:")
        style = "B" if bold_value else ""
        self.set_font("Helvetica", style, 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 7, _pdf_text(value) if value else "N/A")
        self.ln(1)

    def visual_score(self, score, tier):
        """A compact, directly-labelled score bar for the executive page."""
        colors = {"Critical": (224, 108, 117), "High": (224, 108, 117), "Medium": (229, 192, 123), "Low": (152, 195, 121), "Safe": (152, 195, 121)}
        color = colors.get(tier, (97, 175, 239))
        score = max(0, min(100, int(score or 0)))
        x, y, width = 12, self.get_y() + 2, 186
        self.set_fill_color(235, 235, 235)
        self.rect(x, y, width, 10, style="F")
        self.set_fill_color(*color)
        self.rect(x, y, max(4, width * score / 100), 10, style="F")
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*color)
        self.set_xy(12, y + 14)
        self.cell(35, 11, f"{score}/100")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(35, 35, 35)
        self.cell(0, 11, f"{_pdf_text(tier).upper()} RISK", align="L")
        self.ln(27)

    def contribution_chart(self, contributions, flags):
        """Render a compact evidence bar chart with directly labelled values."""
        rows = list(contributions or [])[:5]
        if not rows:
            rows = [{"signal": _pdf_text(flag), "points": 1} for flag in (flags or [])[:5]]
        if not rows:
            return

        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, "Evidence Signal Contribution")
        self.ln(8)
        max_points = max(1, *[float(row.get("points", 1) or 1) for row in rows])
        for row in rows:
            label = _pdf_text(row.get("signal", "Evidence signal"))[:40]
            points = max(0, float(row.get("points", 1) or 1))
            y = self.get_y()
            self.set_font("Helvetica", "", 9)
            self.set_text_color(60, 60, 60)
            self.set_xy(12, y)
            self.cell(58, 6, label)
            self.set_fill_color(235, 235, 235)
            self.rect(72, y + 1.5, 94, 4, style="F")
            self.set_fill_color(97, 175, 239)
            self.rect(72, y + 1.5, max(2, 94 * points / max_points), 4, style="F")
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(35, 35, 35)
            shown_points = int(points) if points.is_integer() else round(points, 1)
            self.set_xy(170, y)
            self.cell(28, 6, f"+{shown_points}", align="R")
            self.ln(7)
        self.ln(3)

    def relay_timeline(self, relay_hops, selected_ip):
        """Render an at-a-glance relay sequence and mark the selected origin IP."""
        hops = list(relay_hops or [])[:6]
        if not hops:
            return
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, "Observed Relay Sequence")
        self.ln(8)
        x, y = 18, self.get_y() + 4
        step = min(31, 166 / max(1, len(hops) - 1))
        for index, hop in enumerate(hops):
            ip = _pdf_text(hop.get("ip") or "No IP")
            selected = ip == _pdf_text(selected_ip)
            if index:
                self.set_draw_color(185, 185, 185)
                self.set_line_width(.5)
                self.line(x - step + 8, y, x - 8, y)
            self.set_fill_color(*(224, 108, 117) if selected else (97, 175, 239))
            self.ellipse(x - 4, y - 4, 8, 8, style="F")
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(35, 35, 35)
            self.set_xy(x - 12, y + 7)
            self.cell(24, 4, f"Hop {index + 1}", align="C")
            self.set_font("Helvetica", "", 6)
            self.set_xy(x - 14, y + 12)
            self.multi_cell(28, 3, ip, align="C")
            x += step
        self.set_y(y + 28)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(102, 102, 102)
        self.multi_cell(0, 4, "The highlighted node is the oldest public IP selected from this email's Received headers. It identifies the original public relay, not a precise physical sender location.")
        self.ln(2)

    def protocol_row(self, protocol, result):
        is_pass = result == "pass"
        color = (152, 195, 121) if is_pass else (224, 108, 117) if result == "fail" else (102, 102, 102)
        label = "PASS" if is_pass else "FAIL" if result == "fail" else "NOT AVAILABLE"
        y = self.get_y()
        self.set_fill_color(245, 245, 245)
        self.rect(12, y, 186, 10, style="F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(35, 35, 35)
        self.set_xy(16, y + 2)
        self.cell(42, 6, protocol)
        self.set_font("Helvetica", "", 10)
        self.cell(62, 6, _pdf_text(result or "none"))
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.cell(70, 6, label, align="R")
        self.ln(12)

    def risk_badge(self, score, tier):
        """Draw a colored risk badge."""
        colors = {
            "Critical": (255, 51, 102),
            "High": (255, 140, 0),
            "Medium": (255, 200, 0),
            "Low": (0, 200, 100),
            "Safe": (0, 200, 100),
        }
        r, g, b = colors.get(tier, (128, 128, 128))

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(r, g, b)
        self.cell(40, 15, f"{score}/100")
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 15, f"  [{_pdf_text(tier).upper()} RISK]")
        self.ln(18)


def generate_report(case_data):
    """
    Generate a forensic PDF report from case data.
    Returns the file path to the generated PDF.
    """
    pdf = ForensicReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    report_id = f"FR-{str(uuid.uuid4())[:8].upper()}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # === Page 1: Executive Summary ===
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(20, 20, 50)
    pdf.cell(0, 12, "Forensic Email Analysis Report")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.ln(7)
    pdf.cell(0, 7, "Executive assessment and preserved technical evidence")
    pdf.ln(10)

    pdf.key_value("Report ID", report_id)
    pdf.key_value("Generated", timestamp)
    pdf.key_value("Case ID", case_data.get("case_id", "N/A"))
    pdf.key_value("Filename", case_data.get("filename", "N/A"))
    pdf.ln(3)

    # Risk Assessment
    pdf.section_title("1. Fraud Assessment")
    fraud_score = case_data.get("fraud_score", 0)
    risk_tier = case_data.get("risk_tier", "Unknown")
    pdf.visual_score(fraud_score, risk_tier)

    # Flags
    flags = case_data.get("flags", [])
    if flags:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 7, "Triggered Flags:")
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 10)
        for flag in flags:
            pdf.set_text_color(224, 108, 117)
            pdf.cell(5, 6, "!")
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 6, f"  {_pdf_text(flag)}")
            pdf.ln(5)
    pdf.ln(5)

    pdf.contribution_chart(case_data.get("risk_contributions", []), flags)

    # AI Explanation
    explanation = case_data.get("llm_explanation", "")
    if explanation:
        pdf.section_title("2. Analyst Explanation")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 6, _pdf_text(explanation))
        pdf.ln(5)

    # === Page 2: Technical Details ===
    pdf.add_page()

    # Header Analysis
    pdf.section_title("3. Email Header Forensics")
    header = case_data.get("header_analysis", {})

    pdf.key_value("From", header.get("from", "N/A"))
    pdf.key_value("To", header.get("to", "N/A"))
    pdf.key_value("Subject", header.get("subject", "N/A"))
    pdf.key_value("Date", header.get("date", "N/A"))
    pdf.key_value("Message-ID", header.get("message_id", "N/A"))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 8, "Authentication Results")
    pdf.ln(7)
    for proto in ["spf", "dkim", "dmarc"]:
        pdf.protocol_row(proto.upper(), header.get(proto, "none"))

    pdf.ln(5)

    # Mismatches
    pdf.key_value("Reply-To Mismatch", "YES" if header.get("reply_to_mismatch") else "No")
    pdf.key_value("Return-Path Mismatch", "YES" if header.get("return_path_mismatch") else "No")
    pdf.ln(5)

    # Origin Trace
    pdf.section_title("4. Origin Trace & Geolocation")
    geo = case_data.get("geo_trace", {})

    pdf.key_value("Earliest Hop IP", geo.get("earliest_hop_ip", "N/A"))
    pdf.key_value("Country", geo.get("country", "N/A"))
    pdf.key_value("City", geo.get("city", "N/A"))
    pdf.key_value("ISP", geo.get("isp", "N/A"))
    pdf.key_value("Organization", geo.get("org", "N/A"))
    pdf.key_value("VPN/Hosting", "YES" if geo.get("is_vpn_or_hosting") else "No")
    pdf.key_value("Domain Age", f"{geo.get('domain_age_days', 'N/A')} days")
    pdf.key_value("Registrar", geo.get("whois_registrar", "N/A"))

    if header.get("relay_hops"):
        # The timeline needs a full visual row. Keep it together rather than
        # allowing its canvas primitives to spill over the page footer.
        if pdf.get_y() > 205:
            pdf.add_page()
        pdf.section_title("5. Relay Path")
        pdf.relay_timeline(header.get("relay_hops", []), geo.get("earliest_hop_ip"))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        for index, hop in enumerate(header.get("relay_hops", [])[:6], start=1):
            label = hop.get("from_host") or "Unknown relay"
            ip = hop.get("ip") or "IP unavailable"
            pdf.cell(0, 6, _pdf_text(f"{index}. {label}  ->  {ip}"))
            pdf.ln(5)

    # === Page 3: Campaign & Chain of Custody ===
    campaign = case_data.get("campaign_data", {})
    linked = campaign.get("linked_emails", [])

    if linked:
        pdf.add_page()
        pdf.section_title("6. Campaign Correlation")
        pdf.key_value("Campaign Size", campaign.get("campaign_size", 0))
        pdf.key_value("Confidence", f"{campaign.get('confidence', 0)}%")
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Linked Emails:")
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 10)
        for email_id in linked:
            pdf.cell(0, 6, f"  - {email_id}")
            pdf.ln(5)

        shared = campaign.get("shared_infra", [])
        if shared:
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Shared Infrastructure:")
            pdf.ln(6)
            pdf.set_font("Helvetica", "", 10)
            for infra in shared:
                pdf.cell(0, 6, f"  - [{infra.get('type', '?')}] {infra.get('node', 'N/A')}")
                pdf.ln(5)

    # Chain of Custody
    pdf.ln(8)
    pdf.set_draw_color(224, 108, 117)
    pdf.set_line_width(0.4)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(4)

    pdf.section_title("7. Chain of Custody")
    pdf.key_value("Report ID", report_id, bold_value=True)
    pdf.key_value("Evidence Hash (SHA-256)", case_data.get("evidence_hash", "N/A"))
    pdf.key_value("Generated At", timestamp)
    pdf.key_value("Integrity Note",
                  "This report was auto-generated. The SHA-256 hash above can be used "
                  "to verify the integrity of the original .eml evidence file.")

    # Save
    filename = f"report_{case_data.get('case_id', 'unknown')}.pdf"
    filepath = os.path.join(REPORT_DIR, filename)
    pdf.output(filepath)

    return filepath
