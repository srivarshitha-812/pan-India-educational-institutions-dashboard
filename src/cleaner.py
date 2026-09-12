"""
Data Cleaner and Normalizer.
"""
import re
from typing import Optional, Tuple, Any
from config import INDIAN_STATES

# State aliases mapping to standard names
STATE_ALIASES = {
    "TELANGANA STATE": "TELANGANA",
    "TG": "TELANGANA",
    "TS": "TELANGANA",
    "AP": "ANDHRA PRADESH",
    "NCT OF DELHI": "DELHI",
    "NEW DELHI": "DELHI",
    "ORISSA": "ODISHA",
    "PONDICHERRY": "PUDUCHERRY",
    "JAMMU & KASHMIR": "JAMMU AND KASHMIR",
    "J&K": "JAMMU AND KASHMIR",
    "ANDAMAN & NICOBAR ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
    "D&NH AND D&D": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
    "DAMAN AND DIU": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
    "DADRA AND NAGAR HAVELI": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
}

def clean_text(text: Optional[str]) -> str:
    """Cleans whitespace, line breaks, and null values."""
    if not text:
        return ""
    text = str(text)
    # Remove HTML tags if present
    text = re.sub(r"<[^>]+>", " ", text)
    # Replace multiple whitespaces and control characters
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_name(name: Optional[str]) -> str:
    """Normalizes an institution name for matching and consistency."""
    if not name:
        return ""
    name = clean_text(name).upper()
    # Normalize common abbreviations
    replacements = {
        r"\bGOVT\b\.?": "GOVERNMENT",
        r"\bINST\b\.?": "INSTITUTE",
        r"\bCOLL\b\.?": "COLLEGE",
        r"\bUNIV\b\.?": "UNIVERSITY",
        r"\bTECH\b\.?": "TECHNOLOGY",
        r"\bENGG\b\.?": "ENGINEERING",
        r"\bMED\b\.?": "MEDICAL",
        r"\bDR\b\.?": "DR",
        r"\bST\b\.?": "ST",
        r"\bSR\b\.?": "SENIOR",
        r"\bJR\b\.?": "JUNIOR",
        r"\bSEC\b\.?": "SECONDARY",
        r"\bHIGH SCH\b\.?": "HIGH SCHOOL",
        r"\bZ\.?P\.?H\.?S\b\.?": "ZP HIGH SCHOOL",
        r"\bZ\.?P\.?P\.?S\b\.?": "ZP PRIMARY SCHOOL",
        r"\bM\.?P\.?P\.?S\b\.?": "MPP SCHOOL",
        r"\bK\.?G\.?B\.?V\b\.?": "KGBV",
        r"\bT\.?S\.?M\.?S\b\.?": "TELANGANA MODEL SCHOOL",
        r"\bT\.?S\.?W\.?R\.?S\b\.?": "TSWREIS",
    }
    for pat, rep in replacements.items():
        name = re.sub(pat, rep, name, flags=re.IGNORECASE)
    # Remove extraneous symbols
    name = re.sub(r"[^\w\s\(\)\-&]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def clean_state(state: Optional[str]) -> str:
    """Standardizes Indian state names."""
    if not state:
        return ""
    s = clean_text(state).upper()
    s = STATE_ALIASES.get(s, s)
    for standard in INDIAN_STATES:
        if s == standard:
            return standard
        # Check if contained
        if s.replace(" ", "") == standard.replace(" ", ""):
            return standard
    return s

def clean_district(district: Optional[str]) -> str:
    """Standardizes district names."""
    if not district:
        return ""
    d = clean_text(district).upper()
    # Remove unwanted suffixes like "DISTRICT", "DIST", "DT"
    d = re.sub(r"\b(DISTRICT|DIST|DT)\b\.?", "", d, flags=re.IGNORECASE)
    return clean_text(d)

def clean_pincode(pincode: Optional[Any]) -> str:
    """Validates and extracts a 6-digit Indian PIN code."""
    if not pincode:
        return ""
    p_str = clean_text(str(pincode))
    match = re.search(r"\b([1-9][0-9]{5})\b", p_str)
    return match.group(1) if match else ""

def clean_coordinates(lat: Any, lon: Any) -> Tuple[Optional[float], Optional[float]]:
    """Validates latitude and longitude within Indian bounds."""
    try:
        if lat is None or lon is None:
            return None, None
        lat_f = float(lat)
        lon_f = float(lon)
        # Bounding box for India: Lat 6 to 38, Lon 68 to 98
        if 6.0 <= lat_f <= 38.5 and 68.0 <= lon_f <= 98.5:
            return round(lat_f, 6), round(lon_f, 6)
    except (ValueError, TypeError):
        pass
    return None, None

def clean_phone(phone: Optional[str]) -> str:
    """Extracts valid phone / mobile numbers."""
    if not phone:
        return ""
    p = clean_text(phone)
    # Remove multiple dashes and spaces
    digits = re.findall(r"\d{10,12}", p)
    return ", ".join(digits) if digits else p

def clean_email(email: Optional[str]) -> str:
    """Validates and cleans email addresses."""
    if not email:
        return ""
    e = clean_text(email).lower()
    matches = re.findall(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", e)
    return ", ".join(matches) if matches else ""

def clean_website(url: Optional[str]) -> str:
    """Standardizes website URLs."""
    if not url:
        return ""
    u = clean_text(url).strip()
    if not u or u.lower() in ["na", "nil", "none", "n/a", "-"]:
        return ""
    if not u.startswith("http://") and not u.startswith("https://"):
        u = "https://" + u
    return u
