"""
Module 6: Privacy, Legal & Compliance Safeguards
- SHA-256 evidence hashing for chain-of-custody
- PII masking for email addresses
"""

import hashlib
import re


def compute_evidence_hash(file_bytes):
    """Compute SHA-256 hash of the raw .eml file for chain-of-custody."""
    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode("utf-8")
    return hashlib.sha256(file_bytes).hexdigest()


def mask_email(email_address, mask=True):
    """Mask an email address for privacy.
    'john.doe@example.com' → 'j***e@example.com'
    """
    if not mask or not email_address or "@" not in email_address:
        return email_address
    name, domain = email_address.split("@", 1)
    if len(name) > 2:
        masked = name[0] + "***" + name[-1]
    else:
        masked = "***"
    return f"{masked}@{domain}"


def mask_ip(ip_address, mask=True):
    """Partially mask an IP address for privacy.
    '185.220.101.4' → '185.220.***'
    """
    if not mask or not ip_address:
        return ip_address
    parts = ip_address.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***"
    return ip_address


def mask_result(result, mask=True):
    """Apply PII masking to an entire analysis result dict."""
    if not mask:
        return result

    masked = dict(result)

    # Mask emails in header_analysis
    header = masked.get("header_analysis", {})
    if isinstance(header, dict):
        header = dict(header)
        for field in ("from", "reply_to", "return_path", "to"):
            if header.get(field):
                header[field] = mask_email(header[field], mask=True)
        masked["header_analysis"] = header

    # Mask IPs in geo_trace
    geo = masked.get("geo_trace", {})
    if isinstance(geo, dict):
        geo = dict(geo)
        if geo.get("earliest_hop_ip"):
            geo["earliest_hop_ip"] = mask_ip(geo["earliest_hop_ip"], mask=True)
        masked["geo_trace"] = geo

    return masked
