from typing import Dict, List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Human-like response templates for different scam tactics
RESPONSE_TEMPLATES = {
    "upi": [
        "I'm not sure what UPI is, can you explain?",
        "Is it safe to share my UPI ID? I'm worried about security.",
        "Can you tell me why you need my UPI ID?",
    ],
    "otp": [
        "Is it safe to share OTP? What will you use it for?",
        "Why do you need my OTP? I've heard it's dangerous.",
        "Can someone misuse my OTP if I share it?",
    ],
    "password": [
        "Should I really share my password? That sounds risky.",
        "Why do you need access to my account password?",
        "I don't think it's safe to share passwords. Right?",
    ],
    "cvv": [
        "You're asking for my CVV? That's the security code, right?",
        "Is it safe to share CVV over message? I'm concerned.",
        "Why would you need my CVV to verify my account?",
    ],
    "link": [
        "Can you explain what this link is for?",
        "Is this link safe to click? Where does it take me?",
        "Why should I click on this? What happens next?",
    ],
    "download": [
        "Is it safe to download that? What does it do?",
        "Why do I need to download an app to verify my account?",
        "Can you explain what this download is for?",
    ],
    "verify": [
        "How will the verification process work?",
        "What happens after I verify? Is my account safe?",
        "Can you explain this verification process?",
    ],
    "account_blocked": [
        "Why is my account blocked? What did I do?",
        "When will my account be unblocked? How long does it take?",
        "Is there another way to resolve this without verification?",
    ],
    "urgent": [
        "Why is this so urgent? What happens if I don't act now?",
        "How much time do I have to respond?",
        "Is this really an emergency? Can it wait?",
    ],
    "default": [
        "Can you explain that more clearly?",
        "I didn't understand. Can you rephrase?",
        "What exactly are you asking me to do?",
        "Can you provide more details?",
        "I'm confused about this. Help me understand.",
    ]
}


def analyze_message_context(message: str, conversation_history: List[Dict] = None) -> Dict[str, bool]:
    """
    Analyze the message context to determine appropriate response tactics.
    
    Returns:
        Dictionary with boolean flags for different scam tactics detected
    """
    msg_lower = message.lower()
    context = {
        "upi": "upi" in msg_lower,
        "otp": "otp" in msg_lower,
        "password": "password" in msg_lower,
        "cvv": "cvv" in msg_lower,
        "link": "link" in msg_lower or "click" in msg_lower or "http" in msg_lower,
        "download": "download" in msg_lower or "install" in msg_lower,
        "verify": "verify" in msg_lower,
        "account_blocked": any(w in msg_lower for w in ["block", "suspended", "locked", "freeze"]),
        "urgent": any(w in msg_lower for w in ["urgent", "immediately", "now", "asap", "today"]),
    }
    return context


def get_agent_reply(
    current_message: str,
    conversation_history: List[Dict] = None,
    previous_replies: List[str] = None
) -> str:
    """
    Generate a human-like reply using context-aware templates.
    
    Strategy:
    - Show confusion and concern (typical victim behavior)
    - Ask clarifying questions (engage without falling into trap)
    - Avoid agreeing to requests directly
    - Adapt based on conversation pattern
    
    Args:
        current_message: Latest message from scammer
        conversation_history: Previous messages in conversation
        previous_replies: Previous AI responses (to avoid repetition)
    
    Returns:
        Human-like response string
    """
    conversation_history = conversation_history or []
    previous_replies = previous_replies or []
    
    # Analyze message context
    context = analyze_message_context(current_message, conversation_history)
    
    # Determine appropriate reply template category
    reply_category = "default"
    for category, detected in context.items():
        if detected and category != "default":
            reply_category = category
            break
    
    # Get templates for this category
    templates = RESPONSE_TEMPLATES.get(reply_category, RESPONSE_TEMPLATES["default"])
    
    # Select a response that hasn't been used recently
    selected_reply = None
    for template in templates:
        if template not in previous_replies[-3:]:  # Avoid last 3 responses
            selected_reply = template
            break
    
    # Fallback to any template if all were used
    if not selected_reply:
        selected_reply = templates[0]
    
    logger.debug(f"Agent selected reply from category '{reply_category}': {selected_reply}")
    return selected_reply


def generate_agent_reply(conversation_history: List[Dict] = None) -> str:
    """
    Legacy function for backward compatibility.
    Generates agent reply based on conversation history.
    """
    conversation_history = conversation_history or []
    
    if not conversation_history:
        return "Why is my account being blocked?"
    
    # Get the last scammer message
    last_scammer_msg = None
    for msg in reversed(conversation_history):
        if msg.get("sender") == "scammer":
            last_scammer_msg = msg
            break
    
    if not last_scammer_msg:
        return "Can you explain that more clearly?"
    
    # Extract all previous AI responses from history
    previous_replies = [
        msg["text"] for msg in conversation_history 
        if msg.get("sender") == "user"
    ]
    
    return get_agent_reply(
        last_scammer_msg["text"],
        conversation_history,
        previous_replies
    )


def should_continue_engagement(
    conversation_history: List[Dict],
    message_count: int,
    max_messages: int = 20
) -> bool:
    """
    Determine if engagement should continue or conclude.
    
    Args:
        conversation_history: Full conversation so far
        message_count: Total number of messages exchanged
        max_messages: Maximum messages before forced conclusion
    
    Returns:
        True if should continue, False if should send final result
    """
    if message_count >= max_messages:
        logger.info(f"Reached max messages ({max_messages}), concluding engagement")
        return False
    
    # Check if enough intelligence has been gathered
    if message_count >= 5:
        # Could add heuristics here to determine if we have enough info
        # For now, continue up to max_messages
        pass
    
    return True


def generate_agent_notes(
    conversation_history: List[Dict],
    extracted_intelligence: Dict
) -> str:
    """
    Generate summary notes about scammer behavior for the final callback.
    
    Args:
        conversation_history: Full conversation
        extracted_intelligence: Extracted intelligence from messages
    
    Returns:
        String summary of scammer tactics observed
    """
    tactics = []
    
    # Analyze all scammer messages
    scammer_messages = [
        msg["text"].lower() for msg in conversation_history 
        if msg.get("sender") == "scammer"
    ]
    
    full_text = " ".join(scammer_messages)
    
    # Identify tactics
    if any(w in full_text for w in ["urgent", "immediately", "now", "asap"]):
        tactics.append("urgency pressure")
    
    if any(w in full_text for w in ["blocked", "suspended", "freeze", "locked"]):
        tactics.append("threat/coercion")
    
    if any(w in full_text for w in ["verify", "confirm", "authenticate"]):
        tactics.append("credential phishing")
    
    if any(w in full_text for w in ["upi", "payment", "transaction"]):
        tactics.append("financial exploitation")
    
    if extracted_intelligence.get("phishingLinks"):
        tactics.append("malware distribution")
    
    if extracted_intelligence.get("bankAccounts"):
        tactics.append("account compromise")
    
    if not tactics:
        tactics.append("social engineering")
    
    notes = f"Scammer employed: {', '.join(tactics)}. "
    
    # Add details based on extracted intelligence
    if extracted_intelligence.get("upiIds"):
        notes += f"Requested UPI ID sharing. "
    if extracted_intelligence.get("bankAccounts"):
        notes += f"Asked for bank details. "
    if extracted_intelligence.get("phishingLinks"):
        notes += f"Provided suspicious links. "
    
    notes += f"Attempted to establish false trust and urgency throughout conversation."
    
    return notes
