"""
Module 3: Origin Traceability & Location Analysis
- IP extraction from Received headers (earliest hop)
- Geolocation via ip-api.com (free, no key required)
- WHOIS lookup for sender domain age
- VPN/hosting provider detection
"""

import re
import os
import requests
import whois
from datetime import datetime, timezone
from functools import lru_cache

# Private/reserved IP ranges that shouldn't be geolocated
PRIVATE_IP_PATTERNS = [
    re.compile(r'^10\.'),
    re.compile(r'^172\.(1[6-9]|2\d|3[01])\.'),
    re.compile(r'^192\.168\.'),
    re.compile(r'^127\.'),
    re.compile(r'^0\.'),
]

# IP attribution is enabled by default. It has a strict short timeout and cache.
# RDAP is the modern, HTTPS replacement for WHOIS and has a strict timeout.
# Legacy WHOIS remains opt-in because providers can block for many seconds.
NETWORK_GEO_ENABLED = os.getenv("ENABLE_NETWORK_ENRICHMENT", "1") == "1"
DOMAIN_AGE_ENABLED = os.getenv("ENABLE_DOMAIN_AGE_ENRICHMENT", "1") == "1"
WHOIS_ENABLED = os.getenv("ENABLE_WHOIS_ENRICHMENT", "1") == "1"


def is_private_ip(ip):
    """Check if an IP address is private/reserved."""
    return any(p.match(ip) for p in PRIVATE_IP_PATTERNS)


def trace_origin(relay_hops, from_domain=None):
    """
    Given relay hops from Module 2, determine the origin IP and geolocate it.
    Also performs WHOIS on the sender domain.
    """
    # Find the earliest external (non-private) IP from relay hops
    earliest_ip = None
    all_ips = []

    for hop in reversed(relay_hops):  # Oldest Received header first
        ip = hop.get("ip")
        if ip and not is_private_ip(ip):
            all_ips.append(ip)
            if earliest_ip is None:
                earliest_ip = ip

    # Geolocation data
    geo_data = {
        "earliest_hop_ip": earliest_ip,
        "all_external_ips": all_ips,
        "country": None,
        "city": None,
        "lat": None,
        "lon": None,
        "isp": None,
        "org": None,
        "is_vpn_or_hosting": False,
        "domain_age_days": None,
        "whois_registrar": None,
        "whois_creation_date": None,
        "dns_records": {},
        "location_detail": None,
    }

    # Geolocate the earliest hop IP
    if earliest_ip and NETWORK_GEO_ENABLED:
        geo_result = geolocate_ip(earliest_ip)
        geo_data.update(geo_result)
        if geo_data.get("lat") is not None and geo_data.get("lon") is not None:
            geo_data["location_detail"] = reverse_geocode(geo_data["lat"], geo_data["lon"])

    # RDAP domain-age lookup is cached and time-bounded; it does not wait on
    # legacy WHOIS services unless explicitly enabled as a fallback.
    if from_domain and DOMAIN_AGE_ENABLED:
        whois_result = lookup_whois(from_domain)
        geo_data.update(whois_result)

    return geo_data


@lru_cache(maxsize=512)
def geolocate_ip(ip):
    """Query ip-api.com for geolocation data. Free tier, no API key needed."""
    result = {
        "country": None,
        "city": None,
        "lat": None,
        "lon": None,
        "isp": None,
        "org": None,
        "is_vpn_or_hosting": False,
    }

    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,city,lat,lon,isp,org,hosting,proxy"},
            timeout=1.5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                result["country"] = data.get("country")
                result["city"] = data.get("city")
                result["lat"] = data.get("lat")
                result["lon"] = data.get("lon")
                result["isp"] = data.get("isp")
                result["org"] = data.get("org")
                result["is_vpn_or_hosting"] = bool(
                    data.get("hosting") or data.get("proxy")
                )
    except requests.RequestException:
        pass  # Graceful failure — geolocation is best-effort

    return result


@lru_cache(maxsize=512)
def reverse_geocode(lat, lon):
    """Best-effort locality lookup for the IP coordinate; no API key needed."""
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 18},
            headers={"User-Agent": "CyberForensix/1.0 forensic-demo"},
            timeout=2,
        )
        if response.status_code == 200:
            address = response.json().get("address", {})
            road = " ".join(filter(None, [address.get("house_number"), address.get("road")]))
            locality = address.get("city") or address.get("town") or address.get("village") or address.get("county")
            parts = [part for part in (road, address.get("suburb"), locality, address.get("state")) if part]
            return ", ".join(parts) or None
    except (requests.RequestException, ValueError, TypeError):
        pass
    return None


@lru_cache(maxsize=512)
def lookup_whois(domain):
    """Look up registration age through RDAP, with optional WHOIS fallback."""
    result = {
        "domain_age_days": None,
        "whois_registrar": None,
        "whois_creation_date": None,
    }

    try:
        response = requests.get(f"https://rdap.org/domain/{domain}", timeout=2)
        if response.status_code == 200:
            record = response.json()
            for event in record.get("events", []):
                if event.get("eventAction") in {"registration", "registered"}:
                    creation_text = event.get("eventDate")
                    if creation_text:
                        creation = datetime.fromisoformat(creation_text.replace("Z", "+00:00"))
                        result["whois_creation_date"] = creation.isoformat()
                        result["domain_age_days"] = max((datetime.now(timezone.utc) - creation).days, 0)
                    break
            for entity in record.get("entities", []):
                if "registrar" in entity.get("roles", []):
                    result["whois_registrar"] = entity.get("handle") or "RDAP registrar"
                    break
    except (requests.RequestException, ValueError, TypeError):
        pass

    if result["domain_age_days"] is None and WHOIS_ENABLED:
        try:
            w = whois.whois(domain)
            creation = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
            if creation:
                creation = creation.replace(tzinfo=timezone.utc)
                result["whois_creation_date"] = str(creation)
                result["domain_age_days"] = max((datetime.now(timezone.utc) - creation).days, 0)
            if w.registrar:
                result["whois_registrar"] = str(w.registrar)
        except Exception:
            pass

    return result
