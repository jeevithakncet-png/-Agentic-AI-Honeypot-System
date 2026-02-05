Agentic Honeypot for Scam Detection & Intelligence Extraction

The Agentic Honeypot System is an AI-powered security API designed to identify online scams, intelligently engage scammers, and extract useful threat intelligence — all without alerting the attacker. Instead of simply blocking suspicious messages, the system actively turns scams into a source of valuable information.

Overview

This project implements a smart, multi-turn conversational honeypot that behaves like a real human user. When a suspicious message is detected, the system hands over the conversation to an AI agent that keeps the scammer engaged while quietly collecting intelligence.

The system can:

Detect scam intent using pattern-based analysis and scoring logic

Automatically activate an AI agent to respond like a real person

Extract sensitive scam-related details such as UPI IDs, bank accounts, phone numbers, and phishing links

Report the collected intelligence to the GUVI evaluation endpoint

Maintain realistic, human-like conversation flow throughout the interaction

Key Features
** Scam Detection**

The system uses a multi-factor scoring mechanism to identify scams. It looks for over 30 different indicators including financial keywords, urgency tactics, requests for sensitive information, threat language, and phishing patterns. Detection is context-aware, meaning it considers the full conversation rather than just single messages.

** AI Agent Engagement**

Once a scam is detected, an AI agent takes control of the conversation. The agent responds naturally using context-aware templates, adapts its replies based on the scammer’s behavior, and avoids revealing that the scam has been detected. This helps keep the attacker engaged longer and reveal more information.

**Intelligence Extraction**

During the conversation, the system automatically extracts useful threat intelligence, including:

Bank account numbers

UPI IDs

Phishing URLs

Indian phone numbers

Email addresses

Cryptocurrency wallet addresses

IP addresses and suspicious keywords

All extracted data is cleaned, validated, and stored per session.

**Security & Authentication
**
The API is protected using API key authentication via request headers. Configuration is handled through environment variables, sessions are securely managed with timeouts, and detailed logs are maintained for debugging and monitoring.
