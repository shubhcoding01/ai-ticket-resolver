# AI Ticket Resolver

Automated IT support ticket resolution system for enterprise desktop support.
Uses Claude AI to classify tickets, PowerShell to auto-resolve common issues,
and a RAG knowledge base to send self-help guides to users.

## Features
- Auto-classifies tickets: app install, antivirus, password reset, network
- Auto-resolves common tickets without human intervention
- Escalates complex issues with AI-generated summary
- Streamlit dashboard for resolution metrics

## Tech Stack
Python, Claude API, LangChain, ChromaDB, PowerShell, Freshdesk API, Streamlit

## Setup
1. Clone this repo
2. Run: pip install -r requirements.txt
3. Copy .env.example to .env and fill in your API keys
4. Run: python main.py