from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MessageModel(BaseModel):
    """Represents a single message in conversation."""
    sender: str = Field(..., description="Message sender: 'scammer' or 'user'")
    text: str = Field(..., min_length=1, description="Message content")
    timestamp: int = Field(..., description="Epoch time in milliseconds")


class MetadataModel(BaseModel):
    """Optional metadata about the conversation."""
    channel: Optional[str] = Field(None, description="SMS/WhatsApp/Email/Chat")
    language: Optional[str] = Field(default="English", description="Message language")
    locale: Optional[str] = Field(default="IN", description="Country/region code")


class ExtractedIntelligenceModel(BaseModel):
    """Intelligence extracted from scam messages."""
    bankAccounts: List[str] = Field(default_factory=list, description="Detected bank account numbers")
    upiIds: List[str] = Field(default_factory=list, description="Detected UPI IDs")
    phishingLinks: List[str] = Field(default_factory=list, description="Detected suspicious links")
    phoneNumbers: List[str] = Field(default_factory=list, description="Detected phone numbers")
    suspiciousKeywords: List[str] = Field(default_factory=list, description="Detected suspicious keywords")


class AnalyzeMessageRequestModel(BaseModel):
    """Request payload for message analysis."""
    sessionId: str = Field(..., description="Unique session identifier")
    message: MessageModel = Field(..., description="Current message to analyze")
    conversationHistory: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Previous messages in conversation"
    )
    metadata: Optional[MetadataModel] = Field(None, description="Optional metadata")


class AgentReplyModel(BaseModel):
    """AI Agent response to scammer."""
    status: str = Field(..., description="Response status: 'success' or 'ignored'")
    reply: Optional[str] = Field(None, description="Agent's reply message")


class FinalResultCallbackModel(BaseModel):
    """Payload sent to GUVI evaluation endpoint."""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligenceModel
    agentNotes: str


class ErrorResponseModel(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
