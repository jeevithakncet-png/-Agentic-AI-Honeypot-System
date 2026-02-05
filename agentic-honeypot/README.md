# Agentic Honeypot for Scam Detection & Intelligence Extraction

An AI-powered REST API system designed to detect scam messages, engage scammers autonomously through intelligent agents, and extract actionable intelligence without revealing detection.

## Overview

This system implements a multi-turn conversational honeypot that:
- Detects scam intent using advanced pattern matching and ML techniques
- Activates an autonomous AI agent to engage scammers
- Extracts intelligence (UPI IDs, bank accounts, phone numbers, phishing links, etc.)
- Reports findings back to the GUVI evaluation endpoint
- Maintains a believable human-like persona throughout conversations

## Features

### 🚨 Scam Detection
- Multi-factor scam scoring system
- Detection of 30+ scam indicators (financial keywords, urgency tactics, sensitive info requests, threat language, etc.)
- Context-aware detection based on conversation patterns
- Threat classification (credential theft, phishing, malware, financial fraud, etc.)

### 🤖 AI Agent Engagement
- Human-like response generation using context-aware templates
- Multi-turn conversation handling
- Dynamic response adaptation based on scammer tactics
- Avoids revealing detection while gathering intelligence

### 📊 Intelligence Extraction
- **Bank Accounts**: Extracts account numbers (9-18 digits)
- **UPI IDs**: Detects UPI payment identifiers
- **Phishing Links**: Captures malicious URLs
- **Phone Numbers**: Extracts Indian phone numbers
- **Email Addresses**: Identifies suspicious email addresses
- **Cryptocurrency**: Detects Bitcoin addresses
- **IP Addresses**: Captures suspicious IPs
- **Keywords**: Identifies suspicious terminology

### 🔐 Security & Authentication
- API key-based authentication (`x-api-key` header)
- Configurable via environment variables
- Secure session management with timeout handling
- Error handling and logging throughout

### 📡 GUVI Callback Integration
- Mandatory callback to GUVI evaluation endpoint
- Comprehensive intelligence payload structure
- Automatic triggering based on conversation depth
- Error recovery and logging

## Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

1. **Clone/Download the repository**
```bash
cd agentic-honeypot
```

2. **Create and activate virtual environment**
```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n honeypot python=3.8
conda activate honeypot
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

Key environment variables:
- `API_KEY`: Your secret API key (change in production!)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `SCAM_SCORE_THRESHOLD`: Minimum score to trigger scam detection (default: 4)
- `MAX_MESSAGES_PER_SESSION`: Maximum conversation messages (default: 20)

## Running the API

### Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check
```
GET /api/health
```
No authentication required. Returns API status and active sessions.

### 2. Analyze Message (Main Endpoint)
```
POST /api/analyze-message
```

**Authentication**: Requires `x-api-key` header

**Request Body**:
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your account will be blocked. Verify immediately.",
    "timestamp": 1707110400000
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": 1707110400000
    },
    {
      "sender": "user",
      "text": "Why will my account be blocked?",
      "timestamp": 1707110460000
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "reply": "Is it safe to share OTP? I am worried."
}
```

Or if not scam:
```json
{
  "status": "ignored",
  "reply": null
}
```

### 3. Session Information
```
GET /api/session/{session_id}
```

**Authentication**: Requires `x-api-key` header

Returns detailed information about a session including extracted intelligence, detection details, and conversation count.

## Request Flow

```
1. Client sends message via /api/analyze-message
                     ↓
2. API validates request & authenticates
                     ↓
3. Scam detection analysis (pattern matching, scoring)
                     ↓
4. If NOT scam → Return {"status": "ignored", "reply": null}
                     ↓
5. If SCAM:
   - Mark session as scam detected
   - Extract intelligence (UPI, bank accounts, links, etc.)
   - Generate agent reply (human-like response)
   - Store in session
                     ↓
6. Check conversation depth & engagement status
                     ↓
7. If max messages reached or engagement complete:
   - Generate agent behavior summary
   - Send final result to GUVI endpoint (mandatory)
   - Mark session as concluded
                     ↓
8. Return agent reply to client
```

## Intelligence Callback (GUVI Endpoint)

When conversation reaches completion (max messages or decision point), the system sends this payload:

```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 5,
  "extractedIntelligence": {
    "bankAccounts": ["9876543210123456"],
    "upiIds": ["scammer@upi", "attacker@ybl"],
    "phishingLinks": ["http://malicious-link.example"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["urgent", "verify", "blocked", "otp"]
  },
  "agentNotes": "Scammer employed: urgency pressure, credential phishing, financial exploitation. Attacker used social engineering tactics with false urgency."
}
```

**Endpoint**: `POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult`

## File Structure

```
agentic-honeypot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application setup
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints with auth & logic
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scam_detector.py # Scam detection logic
│   │   ├── agent.py         # AI agent response generation
│   │   ├── extractor.py     # Intelligence extraction
│   │   └── exceptions.py    # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   └── guvi_callback.py # GUVI endpoint integration
│   └── utils/
│       ├── __init__.py
│       ├── config.py        # Configuration management
│       └── logger.py        # Logging setup
├── tests/
│   └── sample_inputs.json   # Sample test messages
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## Configuration

### Scam Detection Thresholds
Edit `app/utils/config.py` to adjust:
- `SCAM_SCORE_THRESHOLD`: Minimum score (default: 4)
- `MIN_MESSAGES_BEFORE_CALLBACK`: Messages required before sending result
- `MAX_MESSAGES_PER_SESSION`: Maximum conversation length
- `SESSION_TIMEOUT_MINUTES`: Session expiration time

### Detection Keywords
Customize detection patterns in `app/core/scam_detector.py`:
- `FINANCIAL_KEYWORDS`: Financial-related terms
- `URGENCY_KEYWORDS`: Time pressure indicators
- `THREAT_KEYWORDS`: Threat language
- `SENSITIVE_KEYWORDS`: Sensitive data requests

### Agent Responses
Modify human-like responses in `app/core/agent.py`:
- `RESPONSE_TEMPLATES`: Dict of response templates by category
- Customize for different locales/languages

## Testing

### Sample Test Messages
See `tests/sample_inputs.json` for example scam messages.

### Using cURL
```bash
curl -X POST http://localhost:8000/api/analyze-message \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-1",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked. Share your UPI ID immediately.",
      "timestamp": 1707110400000
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/analyze-message",
    json={
        "sessionId": "test-session-1",
        "message": {
            "sender": "scammer",
            "text": "Your account blocked. Verify OTP now.",
            "timestamp": 1707110400000
        },
        "conversationHistory": []
    },
    headers={"x-api-key": "your-api-key"}
)
print(response.json())
```

## Performance Optimizations

1. **Session Cleanup**: Automatic removal of expired sessions
2. **Deduplication**: Removes duplicate intelligence entries
3. **Pattern Caching**: Compiled regex patterns for faster detection
4. **Async Logging**: Non-blocking log operations
5. **Connection Pooling**: Reused HTTP connections for GUVI callback

## Security Considerations

✅ **Implemented**:
- API key authentication on all endpoints (except health)
- Input validation using Pydantic models
- CORS configuration
- Error response sanitization (no stack traces to clients)
- Logging of failed authentication attempts

⚠️ **In Production**:
- Use HTTPS/TLS
- Store API key in secure secret management (AWS Secrets, Azure KV, etc.)
- Implement rate limiting
- Add request signing
- Use database instead of in-memory storage
- Enable comprehensive audit logging

## Troubleshooting

### API Not Responding
```bash
# Check if running on correct port
netstat -ano | findstr :8000

# Restart with verbose logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Authentication Failures
- Verify `x-api-key` header is included
- Confirm API key matches `API_KEY` in `.env`
- Check for extra whitespace in the key

### GUVI Callback Failures
- Verify endpoint URL is correct
- Check network connectivity
- Review logs for timeout/connection errors
- Ensure payload structure matches specification

### Session Not Storing Data
- Check if `SESSION_STORE` is persistent (currently in-memory)
- Verify session ID consistency across requests
- Review logs for session initialization errors

## Future Enhancements

- [ ] LLM-based agent responses (OpenAI, Llama, etc.)
- [ ] Database persistence (PostgreSQL, MongoDB)
- [ ] Redis session caching
- [ ] Real-time notification system
- [ ] Advanced ML-based scam detection
- [ ] Multi-language support
- [ ] Rate limiting & DDoS protection
- [ ] Webhook support for custom integrations
- [ ] Historical analytics dashboard

## Evaluation Criteria

The system is evaluated on:
1. **Scam Detection Accuracy**: False positive/negative rates
2. **Agent Engagement Quality**: Conversation naturalness & depth
3. **Intelligence Extraction**: Completeness & accuracy of extracted data
4. **API Stability**: Uptime & response times
5. **Ethical Behavior**: No impersonation, harassment, or illegal tactics

## License

Developed for GUVI Hackathon - Agentic Honeypot Challenge

## Support

For issues or questions:
- Check logs: `tail -f nohup.out`
- Review API docs: `http://localhost:8000/docs`
- Check environment configuration in `.env`

---

**Important**: This system is designed for security research and fraud detection. Use responsibly and ethically.
