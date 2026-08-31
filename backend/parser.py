"""
Module 2: Email Header & Protocol Analysis
Parses .eml files to extract:
- SPF, DKIM, DMARC authentication results
- Reply-to / Return-path mismatches
- Relay hop chain from Received headers
- URL extraction, urgency word count, attachment detection
"""

import email
import email.policy
import re
from email import message_from_bytes, message_from_string


# Words that phishing emails commonly use to create urgency
URGENCY_WORDS = [
    "urgent", "immediately", "action required", "verify", "suspend",
    "expire", "confirm", "unauthorized", "alert", "warning",
    "locked", "limited", "deadline", "final notice", "act now",
    "compromised", "security", "unusual activity", "update your",
    "click here", "click below", "within 24 hours", "account will be"
]

BRAND_KEYWORDS = ("paypal", "microsoft", "google", "amazon", "apple", "bank", "invoice")


def parse_eml(eml_bytes):
    """Parse a .eml file (as bytes) and return a structured analysis dict."""
    if isinstance(eml_bytes, str):
        msg = message_from_string(eml_bytes, policy=email.policy.default)
    else:
        msg = message_from_bytes(eml_bytes, policy=email.policy.default)

    # Basic envelope fields
    from_addr = _extract_email_addr(msg.get("From", ""))
    to_addr = _extract_email_addr(msg.get("To", ""))
    reply_to = _extract_email_addr(msg.get("Reply-To", ""))
    return_path = _extract_email_addr(msg.get("Return-Path", ""))
    subject = msg.get("Subject", "")
    date = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    # Domain extraction
    from_domain = _get_domain(from_addr)
    reply_to_domain = _get_domain(reply_to)
    return_path_domain = _get_domain(return_path)

    # Authentication results
    auth_results = msg.get("Authentication-Results", "")
    spf = _extract_auth_result(auth_results, "spf")
    dkim = _extract_auth_result(auth_results, "dkim")
    dmarc = _extract_auth_result(auth_results, "dmarc")

    # Mismatch detection
    reply_to_mismatch = bool(reply_to and from_domain and reply_to_domain
                             and reply_to_domain.lower() != from_domain.lower())
    return_path_mismatch = bool(return_path and from_domain and return_path_domain
                                and return_path_domain.lower() != from_domain.lower())

    # Relay hops (from Received headers)
    received_headers = msg.get_all("Received", [])
    relay_hops = _parse_received_headers(received_headers)

    # Body analysis
    body = _get_body_text(msg)
    urls = _extract_urls(body)
    url_domains = [_get_domain_from_url(u) for u in urls]
    url_domain_mismatch = sum(
        1 for d in url_domains
        if d and from_domain and d.lower() != from_domain.lower()
    )

    urgency_count = _count_urgency_words(subject + " " + body)
    has_attachment = _has_attachment(msg)
    suspicious_domain = _is_suspicious_domain(from_domain, subject + " " + body)

    return {
        "from": from_addr,
        "to": to_addr,
        "reply_to": reply_to,
        "return_path": return_path,
        "subject": subject,
        "date": date,
        "message_id": message_id,
        "from_domain": from_domain,
        "spf": spf,
        "dkim": dkim,
        "dmarc": dmarc,
        "reply_to_mismatch": reply_to_mismatch,
        "return_path_mismatch": return_path_mismatch,
        "relay_hops": relay_hops,
        "num_hops": len(relay_hops),
        "num_urls": len(urls),
        "urls": urls[:10],  # Cap at 10 for response size
        "url_domain_mismatch": url_domain_mismatch,
        "urgency_word_count": urgency_count,
        "suspicious_domain": suspicious_domain,
        "has_attachment": int(has_attachment),
        "subject_length": len(subject),
        "body_length": len(body),
        "body_preview": body[:500] if body else "",
        "raw_headers": {
            "authentication_results": auth_results,
            "received": received_headers[:5],
        },
    }


def _extract_email_addr(header_value):
    """Extract bare email address from a header value like 'Name <email@domain>'."""
    if not header_value:
        return ""
    match = re.search(r'<([^>]+)>', str(header_value))
    if match:
        return match.group(1).strip()
    # If no angle brackets, try the whole string as an email
    addr = str(header_value).strip()
    if "@" in addr:
        return addr
    return ""


def _get_domain(email_addr):
    """Extract domain from an email address."""
    if not email_addr or "@" not in email_addr:
        return ""
    return email_addr.split("@")[-1].strip().lower()


def _get_domain_from_url(url):
    """Extract domain from a URL."""
    match = re.search(r'https?://([^/:\s]+)', url)
    if match:
        return match.group(1).lower()
    return ""


def _extract_auth_result(auth_header, mechanism):
    """Extract SPF/DKIM/DMARC result from Authentication-Results header."""
    if not auth_header:
        return "none"
    pattern = rf'{mechanism}=(\w+)'
    match = re.search(pattern, auth_header.lower())
    if match:
        return match.group(1)
    return "none"


def _parse_received_headers(received_headers):
    """Parse Received headers to extract IP addresses and relay chain."""
    hops = []
    # Received headers are inconsistent: some wrap the IP in brackets while
    # others use "from host (203.0.113.9)". Support both forms.
    ip_pattern = re.compile(r'(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])')
    from_pattern = re.compile(r'from\s+(\S+)')

    for i, header in enumerate(received_headers):
        header_str = str(header)
        hop = {"index": i, "raw": header_str[:200]}

        ip_match = ip_pattern.search(header_str)
        if ip_match:
            candidate = ip_match.group(1)
            if all(0 <= int(part) <= 255 for part in candidate.split(".")):
                hop["ip"] = candidate

        from_match = from_pattern.search(header_str)
        if from_match:
            hop["from_host"] = from_match.group(1)

        hops.append(hop)

    return hops


def _get_body_text(msg):
    """Extract plain text body from an email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        body += payload.decode("utf-8", errors="replace")
                    except Exception:
                        body += payload.decode("latin-1", errors="replace")
            elif content_type == "text/html" and not body:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        html = payload.decode("utf-8", errors="replace")
                    except Exception:
                        html = payload.decode("latin-1", errors="replace")
                    body = re.sub(r'<[^>]+>', ' ', html)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                body = payload.decode("utf-8", errors="replace")
            except Exception:
                body = payload.decode("latin-1", errors="replace")
        content_type = msg.get_content_type()
        if content_type == "text/html":
            body = re.sub(r'<[^>]+>', ' ', body)

    return body.strip()


def _extract_urls(text):
    """Extract URLs from text."""
    if not text:
        return []
    url_pattern = re.compile(r'https?://[^\s<>"\']+')
    return url_pattern.findall(text)


def _is_suspicious_domain(domain, text):
    """Detect simple look-alikes without falsely flagging normal domains."""
    if not domain:
        return False
    normalized = domain.replace("0", "o").replace("1", "l")
    brand_in_text = any(brand in text.lower() for brand in BRAND_KEYWORDS)
    brand_in_domain = any(brand in normalized for brand in BRAND_KEYWORDS)
    risky_tokens = ("secure", "verify", "support", "billing", "login", "update", "urgent")
    return (brand_in_text and brand_in_domain and domain != normalized) or (
        brand_in_text and any(token in domain for token in risky_tokens) and "-" in domain
    )


def _count_urgency_words(text):
    """Count urgency/phishing-related words in text."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for word in URGENCY_WORDS:
        count += len(re.findall(re.escape(word), text_lower))
    return count


def _has_attachment(msg):
    """Check if the email has non-text attachments."""
    if not msg.is_multipart():
        return False
    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in disposition.lower():
            return True
        content_type = part.get_content_type()
        if content_type and not content_type.startswith("text/") and not content_type.startswith("multipart/"):
            return True
    return False
