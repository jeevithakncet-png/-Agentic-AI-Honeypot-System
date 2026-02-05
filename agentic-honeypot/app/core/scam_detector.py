import re
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Scam Detection Patterns
FINANCIAL_KEYWORDS = ["bank", "account", "upi", "payment", "transaction", "wallet", "credit", "debit"]
ACTION_KEYWORDS = ["send", "verify", "click", "update", "confirm", "share", "provide", "enter"]
SENSITIVE_KEYWORDS = ["otp", "pin", "password", "cvv", "secret", "code"]
URGENCY_KEYWORDS = ["urgent", "immediately", "now", "asap", "quickly", "today", "blocked", "suspended", "freeze"]
THREAT_KEYWORDS = ["block", "suspend", "freeze", "cancel", "close", "locked", "unauthorized"]
ACTION_REQUEST_KEYWORDS = ["click", "download", "install", "update", "renew"]

URL_REGEX = r"https?://[^\s]+"
BANK_ACCOUNT_REGEX = r"\b\d{9,18}\b"  # Bank accounts typically 9-18 digits
SUSPICIOUS_DOMAIN_REGEX = r"(@[a-zA-Z0-9-]+\.[a-zA-Z]{2,})"  # Suspicious domains


def detect_scam(message: str, conversation_history: list = None) -> tuple:
    """
    Detect if a message contains scam intent using pattern matching and context.
    
    Returns:
        tuple: (is_scam: bool, reasons: list, score: int)
    """
    msg = message.lower()
    score = 0
    reasons = []
    
    # Financial context
    financial_matches = sum(1 for w in FINANCIAL_KEYWORDS if w in msg)
    if financial_matches > 0:
        score += financial_matches
        reasons.append("financial context")
    
    # Action requested
    action_matches = sum(1 for w in ACTION_KEYWORDS if w in msg)
    if action_matches > 0:
        score += action_matches
        reasons.append("action requested")
    
    # Sensitive information request (HIGH WEIGHT)
    sensitive_matches = sum(1 for w in SENSITIVE_KEYWORDS if w in msg)
    if sensitive_matches > 0:
        score += sensitive_matches * 3
        reasons.append("sensitive info request")
    
    # Urgency/Threat tactics (HIGH WEIGHT)
    urgency_matches = sum(1 for w in URGENCY_KEYWORDS if w in msg)
    threat_matches = sum(1 for w in THREAT_KEYWORDS if w in msg)
    if urgency_matches > 0:
        score += urgency_matches * 2
        reasons.append("urgency/threat tactics")
    if threat_matches > 0:
        score += threat_matches * 2
        if "urgency/threat tactics" not in reasons:
            reasons.append("threat language")
    
    # External links (HIGH WEIGHT)
    if re.search(URL_REGEX, msg):
        score += 3
        reasons.append("external link detected")
    
    # Suspicious domains
    if re.search(SUSPICIOUS_DOMAIN_REGEX, msg):
        score += 2
        reasons.append("suspicious domain")
    
    # Action request for links/downloads (HIGH WEIGHT)
    action_request_matches = sum(1 for w in ACTION_REQUEST_KEYWORDS if w in msg)
    if action_request_matches > 0:
        score += action_request_matches * 2
        reasons.append("malicious action request")
    
    # Check for combination of financial + action + urgency (typical scam pattern)
    has_financial = any(w in msg for w in FINANCIAL_KEYWORDS)
    has_action = any(w in msg for w in ACTION_KEYWORDS)
    has_urgency = any(w in msg for w in URGENCY_KEYWORDS)
    
    if has_financial and has_action and has_urgency:
        score += 5
        reasons.append("classic scam pattern detected")
    
    # Context-aware detection: Check if previous message was user resistance
    if conversation_history:
        try:
            # If scammer is escalating despite user hesitation
            for msg_obj in conversation_history[-3:]:  # Check last 3 messages
                if msg_obj.get("sender") == "user" and any(w in msg_obj.get("text", "").lower() for w in ["worried", "doubt", "safe", "hesitate", "not sure"]):
                    if any(w in msg for w in URGENCY_KEYWORDS + THREAT_KEYWORDS):
                        score += 2
                        reasons.append("escalation despite user hesitation")
        except Exception as e:
            logger.debug(f"Error during context-aware detection: {e}")
    
    logger.debug(f"Message score: {score}, Reasons: {reasons}")
    
    return score >= 4, reasons, score


def get_scam_details(message: str) -> dict:
    """Get detailed scam classification."""
    msg = message.lower()
    
    scam_type = []
    if any(w in msg for w in ["otp", "password", "pin", "cvv"]):
        scam_type.append("credential theft")
    if any(w in msg for w in ["click", "download", "link"]):
        scam_type.append("malware distribution")
    if any(w in msg for w in ["bank", "account", "upi", "payment"]):
        scam_type.append("financial fraud")
    if any(w in msg for w in ["verify", "confirm", "update"]):
        scam_type.append("phishing")
    
    return {"types": scam_type if scam_type else ["unknown scam"]}
