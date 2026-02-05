from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from app.models.schemas import (
    AnalyzeMessageRequestModel,
    AgentReplyModel,
    ErrorResponseModel,
    ExtractedIntelligenceModel
)
from app.core.scam_detector import detect_scam, get_scam_details
from app.core.agent import generate_agent_reply, should_continue_engagement, generate_agent_notes
from app.core.extractor import extract_intelligence, enrich_intelligence
from app.services.guvi_callback import send_final_result
from app.utils.config import settings
from app.utils.logger import get_logger
from app.core.exceptions import AuthenticationException, CallbackException

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# In-memory session storage (appropriate for hackathon)
# Format: {session_id: {"messages": [...], "intelligence": {...}, "created_at": datetime, "last_activity": datetime, "engagement_concluded": bool}}
SESSION_STORE: Dict[str, Dict[str, Any]] = {}


def authenticate_request(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Validate API key from request header.
    
    Args:
        x_api_key: API key from x-api-key header
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header"
        )
    
    if x_api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True


def initialize_session(session_id: str) -> None:
    """Initialize a new session."""
    SESSION_STORE[session_id] = {
        "messages": [],
        "intelligence": {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": [],
            "emailAddresses": [],
            "bitcoinAddresses": [],
            "ipAddresses": []
        },
        "agent_replies": [],
        "scam_detected": False,
        "detection_details": {},
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "engagement_concluded": False,
        "scam_score": 0
    }
    logger.info(f"Initialized new session: {session_id}")


def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Get existing session or create new one."""
    if session_id not in SESSION_STORE:
        initialize_session(session_id)
    else:
        SESSION_STORE[session_id]["last_activity"] = datetime.now()
    
    return SESSION_STORE[session_id]


def cleanup_old_sessions() -> None:
    """Remove sessions that have timed out."""
    timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
    current_time = datetime.now()
    
    expired_sessions = [
        sid for sid, data in SESSION_STORE.items()
        if current_time - data["last_activity"] > timeout
    ]
    
    for session_id in expired_sessions:
        logger.info(f"Cleaning up expired session: {session_id}")
        del SESSION_STORE[session_id]


@router.post("/analyze-message", response_model=AgentReplyModel)
def analyze_message(
    payload: AnalyzeMessageRequestModel,
    x_api_key: Optional[str] = Header(None)
) -> AgentReplyModel:
    """
    Analyze incoming message and generate AI agent response.
    
    Workflow:
    1. Validate API key
    2. Extract and validate request
    3. Detect scam intent
    4. If scam detected, activate agent
    5. Extract intelligence
    6. Send callback if engagement complete
    
    Args:
        payload: Request payload with message and conversation history
        x_api_key: API key for authentication
    
    Returns:
        Agent reply with status and optional message
    """
    try:
        # Authenticate
        authenticate_request(x_api_key)
        
        # Cleanup old sessions
        cleanup_old_sessions()
        
        session_id = payload.sessionId
        message_text = payload.message.text
        sender = payload.message.sender
        conversation_history = payload.conversationHistory or []
        
        logger.info(f"Processing message for session {session_id}, sender: {sender}")
        
        # Get or create session
        session = get_or_create_session(session_id)
        
        # Add message to session history
        session["messages"].append({
            "sender": sender,
            "text": message_text,
            "timestamp": payload.message.timestamp
        })
        
        total_messages = len(session["messages"])
        
        # Detect scam intent
        is_scam, reasons, score = detect_scam(message_text, conversation_history)
        session["scam_score"] = max(session["scam_score"], score)
        
        logger.debug(f"Scam detection - Score: {score}, Scam: {is_scam}, Reasons: {reasons}")
        
        # If scam not detected on first message, ignore
        if not is_scam:
            logger.info(f"Non-scam message in session {session_id}, ignoring")
            return AgentReplyModel(status="ignored", reply=None)
        
        # Mark scam as detected
        if not session["scam_detected"]:
            session["scam_detected"] = True
            session["detection_details"] = {
                "score": score,
                "reasons": reasons,
                "message_index": total_messages,
                "scam_types": get_scam_details(message_text)
            }
            logger.warning(f"🚨 SCAM DETECTED in session {session_id}: {reasons}")
        
        # Extract intelligence from current message and full conversation
        full_conversation = conversation_history + [
            {
                "sender": sender,
                "text": message_text,
                "timestamp": payload.message.timestamp
            }
        ]
        
        new_intelligence = extract_intelligence(message_text, full_conversation)
        
        # Merge intelligence
        for key in new_intelligence:
            if key in session["intelligence"]:
                session["intelligence"][key].extend(new_intelligence[key])
                session["intelligence"][key] = list(set(session["intelligence"][key]))  # Deduplicate
        
        logger.debug(f"Accumulated intelligence: {session['intelligence']}")
        
        # Generate agent reply
        agent_reply = generate_agent_reply(conversation_history)
        session["agent_replies"].append(agent_reply)
        
        logger.info(f"Agent reply for session {session_id}: {agent_reply}")
        
        # Determine if engagement should continue or conclude
        should_continue = should_continue_engagement(
            full_conversation,
            total_messages,
            settings.MAX_MESSAGES_PER_SESSION
        )
        
        # Send final callback if engagement is complete
        if not should_continue and not session["engagement_concluded"]:
            try:
                # Generate notes about scammer behavior
                agent_notes = generate_agent_notes(full_conversation, session["intelligence"])
                
                logger.info(f"Concluding engagement for session {session_id}")
                logger.debug(f"Agent notes: {agent_notes}")
                
                # Send to GUVI evaluation endpoint
                success = send_final_result(
                    session_id=session_id,
                    intelligence=session["intelligence"],
                    total_messages=total_messages,
                    agent_notes=agent_notes,
                    scam_detected=True
                )
                
                if success:
                    session["engagement_concluded"] = True
                    logger.info(f"✓ Final result sent for session {session_id}")
                else:
                    logger.warning(f"⚠ Final result callback may have failed for {session_id}")
                    
            except CallbackException as e:
                logger.error(f"Callback error for session {session_id}: {e}")
                # Don't fail the response, but log the error
        
        # Check if we should conclude without explicit max messages
        elif total_messages >= settings.MIN_MESSAGES_BEFORE_CALLBACK and not session["engagement_concluded"]:
            # Optional: implement smarter logic to decide when to conclude
            pass
        
        return AgentReplyModel(status="success", reply=agent_reply)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/session/{session_id}")
def get_session_info(
    session_id: str,
    x_api_key: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get information about a specific session.
    Requires authentication.
    """
    authenticate_request(x_api_key)
    
    if session_id not in SESSION_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    session = SESSION_STORE[session_id]
    return {
        "sessionId": session_id,
        "messageCount": len(session["messages"]),
        "scamDetected": session["scam_detected"],
        "detectionDetails": session["detection_details"],
        "extractedIntelligence": session["intelligence"],
        "engagementConcluded": session["engagement_concluded"],
        "createdAt": session["created_at"].isoformat(),
        "lastActivity": session["last_activity"].isoformat()
    }


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint (no authentication required)."""
    return {
        "status": "running",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "sessions": len(SESSION_STORE)
    }
