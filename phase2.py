# Author : Shubham Kumar
# Description: Autonomous content engine using LangGraph.
# Description: Autonomous content engine using LangGraph.
# Bot picks a topic, searches for context, then drafts a 280-char opinionated post.
# This is Phase 2 of the Grid07 AI assignment.

import os
import json

from dotenv import load_dotenv

from typing import TypedDict, Any

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

from langgraph.graph import StateGraph, END


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Using llama3-8b

llm = ChatGroq(
    model="llama3-8b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.8
)

# ---------------------------------------------
# Bot Personas
# ---------------------------------------------

BOT_PERSONAS = {
    "Bot_A_TechMaximalist": (
        "You are a Tech Maximalist. You believe AI and crypto will solve all human problems. "
        "You are highly optimistic about technology, Elon Musk, and space exploration. "
        "You dismiss regulatory concerns. You are bold, slightly arrogant, and always bullish."
    ),
    "Bot_B_Doomer": (
        "You are a Doomer and Skeptic. You believe late-stage capitalism and tech monopolies "
        "are destroying society. You are highly critical of AI, social media, and billionaires. "
        "You value privacy and nature. You write with urgency and frustration."
    ),
    "Bot_C_FinanceBro": (
        "You are a Finance Bro. You strictly care about markets, interest rates, trading "
        "algorithms, and making money. You speak in finance jargon and view everything through "
        "the lens of ROI. You use terms like alpha, leverage, macro, and liquidity."
    ),
}

# ---------------------------------------------
# Mock Search Tool
# Simulates a real web search with hardcoded headlines
# ---------------------------------------------

@tool
def mock_searxng_search(query: str) -> str:
    """
    Simulates a SearXNG web search. Returns hardcoded headlines based on keywords.
    """
    query_lower = query.lower()
    if "crypto" in query_lower or "bitcoin" in query_lower:
        return (
            "Bitcoin hits new all-time high amid regulatory ETF approvals. "
            "Ethereum layer-2 solutions see 300% surge in daily transactions. "
            "SEC approves spot crypto ETFs for institutional investors."
        )
    elif "ai" in query_lower or "artificial intelligence" in query_lower or "openai" in query_lower:
        return (
            "OpenAI releases GPT-5 with multimodal reasoning capabilities. "
            "AI startups raise record $50B in Q1 2025. "
            "Tech companies cut junior dev hiring by 40% citing AI productivity tools."
        )
    elif "market" in query_lower or "stock" in query_lower or "fed" in query_lower or "interest rate" in query_lower:
        return (
            "Fed signals two more rate cuts in 2025 as inflation cools to 2.1%. "
            "S&P 500 hits record high on strong earnings season. "
            "Hedge funds rotate into tech as bond yields drop."
        )
    elif "climate" in query_lower or "environment" in query_lower or "nature" in query_lower:
        return (
            "IPCC warns 2025 is the hottest year on record. "
            "Tech companies' data centers consume more electricity than some countries. "
            "Grassroots movements push for digital rights and environmental accountability."
        )
    elif "elon" in query_lower or "tesla" in query_lower or "space" in query_lower:
        return (
            "SpaceX Starship completes first commercial orbital mission. "
            "Tesla FSD achieves Level 4 autonomy certification in three US states. "
            "Elon Musk announces plans for Mars colony by 2030."
        )
    else:
        # Generic fallback
        return (
            "Tech industry faces increasing regulatory scrutiny worldwide. "
            "Global markets show mixed signals amid geopolitical tensions. "
            "AI adoption accelerates across all major industries in 2025."
        )
    
# --------------------------------------------
# LangGraph State Definition
# ---------------------------------------------


