import re
import os
import sys
from typing import Dict, List

# Ensure project root is on sys.path so `from app...` imports work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from app.utils.logger import get_logger
except Exception:
    # Fallback: load logger module directly from file when package imports fail
    import importlib.util

    logger_path = os.path.join(ROOT, "app", "utils", "logger.py")
    spec = importlib.util.spec_from_file_location("app.utils.logger", logger_path)
    logger_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(logger_mod)
    get_logger = getattr(logger_mod, "get_logger")

logger = get_logger(__name__)

# Regex patterns for intelligence extraction
UPI_REGEX = r"\b[\w.\-]{2,}@[a-zA-Z]{2,}\b"  # UPI IDs like name@upi, user@ybl, etc.
URL_REGEX = r"https?://[^\s]+"  # HTTP/HTTPS links
PHONE_REGEX = r"(?:\+91|91|0)?\s*[6-9]\d{9}"  # Indian phone numbers
BANK_ACCOUNT_REGEX = r"\b\d{9,18}\b"  # Bank account numbers (9-18 digits)
EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"  # Email addresses
BITCOIN_REGEX = r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"  # Bitcoin addresses
IP_ADDRESS_REGEX = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"  # IP addresses

# Suspicious keywords that indicate scam tactics
SUSPICIOUS_KEYWORDS = [
    "urgent", "verify", "blocked", "suspended", "freeze", "confirm", 
    "immediate", "claim", "update", "click", "download", "authenticate",
    "password", "otp", "pin", "cvv", "secret", "validate", "activate",
    "renew", "expire", "unauthorized", "secure", "protect", "danger",
    "limited", "today", "now", "asap", "hurry", "quickly", "immediately"
]


def clean_intelligence(intel_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Remove duplicates and invalid entries."""
    cleaned = {}
    for key, values in intel_dict.items():
        # Remove duplicates and convert to lowercase for consistency
        unique_values = list(set(str(v).lower().strip() for v in values if v))
        cleaned[key] = [v for v in unique_values if v]  # Remove empty strings
    return cleaned


def extract_intelligence(text: str, full_conversation: list = None) -> Dict[str, List[str]]:
    """
    Extract intelligence from scam message.
    
    Returns:
        Dictionary with extracted: bankAccounts, upiIds, phishingLinks, 
        phoneNumbers, suspiciousKeywords
    """
    intelligence = {
        "bankAccounts": [],
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "suspiciousKeywords": [],
        "emailAddresses": [],
        "bitcoinAddresses": [],
        "ipAddresses": []
    }
    
    try:
        # Extract UPI IDs
        upi_matches = re.findall(UPI_REGEX, text, re.IGNORECASE)
        intelligence["upiIds"].extend(upi_matches)
        
        # Extract phishing links
        link_matches = re.findall(URL_REGEX, text)
        intelligence["phishingLinks"].extend(link_matches)
        
        # Extract phone numbers (Indian format)
        phone_matches = re.findall(PHONE_REGEX, text)
        intelligence["phoneNumbers"].extend(phone_matches)
        
        # Extract bank accounts (consecutive digits, typically 9-18)
        account_matches = re.findall(BANK_ACCOUNT_REGEX, text)
        # Filter: remove very short numbers and timestamps
        valid_accounts = [
            acc for acc in account_matches 
            if 9 <= len(acc) <= 18 and not is_likely_timestamp(acc)
        ]
        intelligence["bankAccounts"].extend(valid_accounts)
        
        # Extract email addresses
        email_matches = re.findall(EMAIL_REGEX, text)
        # Filter out common non-suspicious emails
        suspicious_emails = [
            e for e in email_matches 
            if not any(domain in e.lower() for domain in ["@gmail.com", "@yahoo.com", "@outlook.com"])
            or any(keyword in text.lower() for keyword in SUSPICIOUS_KEYWORDS)
        ]
        intelligence["emailAddresses"].extend(suspicious_emails)
        
        # Extract Bitcoin addresses if present
        bitcoin_matches = re.findall(BITCOIN_REGEX, text)
        intelligence["bitcoinAddresses"].extend(bitcoin_matches)
        
        # Extract IP addresses
        ip_matches = re.findall(IP_ADDRESS_REGEX, text)
        intelligence["ipAddresses"].extend(ip_matches)
        
        # Extract suspicious keywords
        text_lower = text.lower()
        found_keywords = [
            kw for kw in SUSPICIOUS_KEYWORDS 
            if kw in text_lower
        ]
        intelligence["suspiciousKeywords"].extend(found_keywords)
        
        # Extract from full conversation for better context
        if full_conversation:
            for msg in full_conversation:
                msg_text = msg.get("text", "")
                intelligence["upiIds"].extend(re.findall(UPI_REGEX, msg_text, re.IGNORECASE))
                intelligence["phishingLinks"].extend(re.findall(URL_REGEX, msg_text))
                intelligence["phoneNumbers"].extend(re.findall(PHONE_REGEX, msg_text))
                intelligence["emailAddresses"].extend(re.findall(EMAIL_REGEX, msg_text))
        
        # Clean and deduplicate
        intelligence = clean_intelligence(intelligence)
        
        logger.debug(f"Extracted intelligence: {intelligence}")
        
    except Exception as e:
        logger.error(f"Error during intelligence extraction: {e}")
    
    return intelligence


def is_likely_timestamp(number_str: str) -> bool:
    """Check if a number string is likely a timestamp rather than account."""
    if len(number_str) > 13:
        return False  # Timestamps rarely exceed 13 digits
    
    # Timestamps usually very large (1000000000+)
    try:
        num = int(number_str)
        return num > 1000000000  # Unix timestamp threshold
    except:
        return False


def enrich_intelligence(intelligence: Dict, context: str = "") -> Dict:
    """
    Enrich extracted intelligence with additional analysis.
    
    Args:
        intelligence: Previously extracted intelligence
        context: Additional context about the conversation
    
    Returns:
        Enhanced intelligence dictionary
    """
    enriched = intelligence.copy()
    
    # Add confidence scores or additional metadata if needed
    enriched["extracted_at"] = None  # Timestamp can be added by routes
    
    # Classify intelligence severity
    if enriched.get("bankAccounts") or enriched.get("bitcoinAddresses"):
        enriched["severity"] = "critical"
    elif enriched.get("phoneNumbers") or enriched.get("emailAddresses"):
        enriched["severity"] = "high"
    else:
        enriched["severity"] = "medium"
    
    return enriched


if __name__ == "__main__":
    # Test the extraction functions
    test_messages = [
        "Urgent! Your account is suspended. Click https://verify-bank.com to verify. Call +919876543210 immediately!",
        "Please confirm your UPI: user@ybl from account 123456789012",
        "Bitcoin address: 1A1z7agoat2xSfEQTEGjQjeonZvprLP5Vb",
        "Your IP 192.168.1.1 has suspicious activity. OTP: 123456"
    ]
    
    print("=" * 80)
    print("SCAM MESSAGE INTELLIGENCE EXTRACTION TEST")
    print("=" * 80)
    
    for idx, msg in enumerate(test_messages, 1):
        print(f"\n[Message {idx}] {msg}")
        intelligence = extract_intelligence(msg)
        enriched = enrich_intelligence(intelligence)
        
        print(f"\nExtracted Intelligence:")
        for key, value in intelligence.items():
            if value:  # Only print non-empty fields
                print(f"  {key}: {value}")
        print(f"  Severity: {enriched.get('severity', 'unknown')}")
    
    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)
