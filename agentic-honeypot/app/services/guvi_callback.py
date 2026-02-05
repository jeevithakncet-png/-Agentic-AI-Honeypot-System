import requests
import json
from typing import Dict, List, Optional
from app.utils.config import settings
from app.utils.logger import get_logger
from app.core.exceptions import CallbackException

logger = get_logger(__name__)


def send_final_result(
    session_id: str,
    intelligence: Dict,
    total_messages: int,
    agent_notes: str = "",
    scam_detected: bool = True
) -> bool:
    """
    Send final extracted intelligence to GUVI evaluation endpoint.
    
    Args:
        session_id: Unique session identifier
        intelligence: Extracted intelligence dictionary
        total_messages: Total messages exchanged in session
        agent_notes: Summary of scammer behavior
        scam_detected: Whether scam was confirmed
    
    Returns:
        bool: True if callback was successful, False otherwise
    """
    payload = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": intelligence.get("bankAccounts", []),
            "upiIds": intelligence.get("upiIds", []),
            "phishingLinks": intelligence.get("phishingLinks", []),
            "phoneNumbers": intelligence.get("phoneNumbers", []),
            "suspiciousKeywords": intelligence.get("suspiciousKeywords", [])
        },
        "agentNotes": agent_notes or "Scammer attempted fraud through social engineering."
    }

    try:
        logger.info(f"Sending final result for session {session_id}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            settings.GUVI_ENDPOINT,
            json=payload,
            timeout=settings.GUVI_CALLBACK_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            logger.info(f"✓ Final result successfully sent for session {session_id}")
            return True
        else:
            logger.warning(
                f"Final result callback returned status {response.status_code}: {response.text}"
            )
            return False
            
    except requests.Timeout:
        logger.error(f"GUVI callback timeout for session {session_id}")
        raise CallbackException(f"Callback timeout after {settings.GUVI_CALLBACK_TIMEOUT}s")
    except requests.ConnectionError as e:
        logger.error(f"Failed to connect to GUVI endpoint: {e}")
        raise CallbackException(f"Connection error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during GUVI callback: {e}")
        raise CallbackException(f"Callback failed: {str(e)}")
