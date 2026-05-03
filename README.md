<!-- # AI Ticket Resolver

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
4. Run: python main.py -->


# 🎫 AI Ticket Resolver — Automated IT Support System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Claude AI](https://img.shields.io/badge/Claude-AI-orange?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**An AI-powered IT support ticket automation system built for enterprise desktop support.**
Automatically classifies, resolves, and escalates support tickets using Claude AI,
PowerShell automation, and a RAG-based knowledge base.

[Demo Mode](#demo-mode) • [Live Mode](#live-mode) • [Dashboard](#dashboard) • [Architecture](#architecture)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Demo Mode](#demo-mode)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Dashboard](#dashboard)
- [Live Mode](#live-mode)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Testing](#testing)
- [Results](#results)

---

## 🌟 Overview

This project was built based on real-world experience in enterprise desktop support
at ICICI Bank. Every day, IT support teams manually process hundreds of tickets —
app installations, antivirus updates, password resets, VPN issues — that follow
the same patterns every time.

This system automates that entire workflow:

1. Reads tickets from Freshdesk every 5 minutes
2. Classifies them using Claude AI (or rule-based fallback offline)
3. Auto-resolves common issues remotely via PowerShell scripts
4. Searches the knowledge base and sends self-help guides to users
5. Escalates complex issues to engineers with full AI-generated summaries
6. Logs everything and displays live metrics on a Streamlit dashboard

> **Demo mode available** — run the full system with zero API keys.
> The demo processes 10 realistic ICICI Bank support tickets end to end.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 AI Classification | Claude AI classifies tickets into 10 categories with priority detection |
| ⚡ Auto-Resolution | PowerShell scripts resolve common issues remotely without human involvement |
| 📚 Knowledge Base | RAG system searches IT guides and sends self-help steps to users |
| 📧 Email Notifications | Professional HTML emails sent to users on resolution or escalation |
| 🔺 Smart Escalation | Complex tickets escalated with full AI summary for engineers |
| 📊 Live Dashboard | Streamlit dashboard with charts, metrics, and ticket logs |
| 🏃 Demo Mode | Full system simulation — no API keys or real systems needed |
| 🔁 Fallback Classifier | Keyword-based rule classifier works offline when API is unavailable |
| 🛡️ Force Escalation | Critical keywords (ransomware, data breach) trigger immediate escalation |
| ⏰ After-Hours Routing | Tickets outside business hours get acknowledgement and next-day escalation |
| 📝 Full Audit Trail | Every action logged to SQLite with timestamps and resolution method |
| 🔧 Dry Run Mode | Test the system without closing real tickets or running real scripts |

---

## 🚀 Demo Mode

The demo runs the **complete real pipeline** with 10 sample ICICI Bank tickets.
No API keys, no Freshdesk account, no real machines needed.

```bash