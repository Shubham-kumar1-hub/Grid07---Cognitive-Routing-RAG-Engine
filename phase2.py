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
    model="llama-3.1-8b-instant",
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

class PostState(TypedDict):
    bot_id: str
    persona: str
    search_query: str
    search_results: str
    final_post: dict[str, Any]


# --------------------------------------------
# Node 1: Decide Search Query
# LLM reads the persona and decides what to post about today
# ---------------------------------------------

def decide_search_node(state: PostState) -> PostState:
    print(f"\n[NODE 1] Deciding search topic for {state['bot_id']}...")

    system_prompt = f"""
You are the following social media bot persona:
{state['persona']}
 
Your task: Decide what ONE topic you want to post about today.
Then generate a short 3-5 word search query to find recent news on that topic.
 
Respond with ONLY the search query. No explanation, no extra text.
Example: "AI replacing software jobs 2025"
"""
 
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="What do you want to search for today? Give me just the search query.")
    ]
 
    response = llm.invoke(messages)
    search_query = response.content.strip().strip('"')
 
    print(f"[NODE 1] Search query decided: \"{search_query}\"")
    return {**state, "search_query": search_query}

# --------------------------------------------
# Node 2: Execute Web Search
# Calls the mock search tool with the query from Node 1
# ---------------------------------------------

def web_search_node(state: PostState) -> PostState:
    print(f"\n[NODE 2] Running search for: \"{state['search_query']}\"")
 
    # Calling the mock search tool
    search_results = mock_searxng_search.invoke({"query": state["search_query"]})
 
    print(f"[NODE 2] Search results: {search_results}")
    return {**state, "search_results": search_results}

# ---------------------------------------------
# Node 3: Draft the Post
# LLM uses persona + search results to write a 280-char post
# Output is strict JSON
# ---------------------------------------------
 
def draft_post_node(state: PostState) -> PostState:
    print(f"\n[NODE 3] Drafting post for {state['bot_id']}...")
 
    system_prompt = f"""
You are this social media bot:
{state['persona']}
 
You have found the following recent news:
{state['search_results']}
 
Write a highly opinionated social media post based on this news.
Stay 100% in character. Be bold and direct.
 
STRICT RULES:
1. The post must be UNDER 280 characters
2. You MUST respond with ONLY a valid JSON object - nothing else before or after it
3. The JSON must follow this exact format:
{{"bot_id": "{state['bot_id']}", "topic": "<the topic you are posting about>", "post_content": "<your 280-char post>"}}
 
Do NOT include markdown, backticks, or any explanation. Just the raw JSON object.
"""
 
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate the post now. Return ONLY the JSON object.")
    ]
 
    response = llm.invoke(messages)
    raw_output = response.content.strip()
 
    print(f"[NODE 3] Raw LLM output: {raw_output}")
 
    # Parse the JSON - handles edge cases where LLM adds backticks
    try:
        # Strip markdown code blocks if LLM adds them anyway
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
            raw_output = raw_output.strip()
 
        parsed = json.loads(raw_output)
        print(f"[NODE 3] Parsed JSON successfully.")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing failed: {e}")
        # Fallback structure so the graph doesn't crash
        parsed = {
            "bot_id": state["bot_id"],
            "topic": state["search_query"],
            "post_content": raw_output[:280]
        }
 
    return {**state, "final_post": parsed}
 
 
# --------------------------------------------
# Building the LangGraph State Machine
# --------------------------------------------
 
def build_post_graph() -> StateGraph:
    graph = StateGraph(PostState)
 
    # Register nodes
    graph.add_node("decide_search", decide_search_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("draft_post", draft_post_node)
 
    # Defining the flow: linear pipeline
    graph.set_entry_point("decide_search")
    graph.add_edge("decide_search", "web_search")
    graph.add_edge("web_search", "draft_post")
    graph.add_edge("draft_post", END)
 
    return graph.compile()
 
 
def run_content_engine(bot_id: str) -> dict:
    """
    Run the full LangGraph pipeline for a given bot.
    Returns the final JSON post object.
    """
    if bot_id not in BOT_PERSONAS:
        raise ValueError(f"Unknown bot_id: {bot_id}. Choose from {list(BOT_PERSONAS.keys())}")
 
    initial_state: PostState = {
        "bot_id": bot_id,
        "persona": BOT_PERSONAS[bot_id],
        "search_query": "",
        "search_results": "",
        "final_post": {}
    }
 
    print(f"\n{'='*60}")
    print(f"Running Content Engine for: {bot_id}")
    print(f"{'='*60}")
 
    graph = build_post_graph()
    final_state = graph.invoke(initial_state)
 
    return final_state["final_post"]

# --------------------------------------------
# Quick test / demo run
# --------------------------------------------
 
if __name__ == "__main__":
    # Testing with Bot A (Tech Maximalist)
    result_a = run_content_engine("Bot_A_TechMaximalist")
    print(f"\n[FINAL OUTPUT - Bot A]")
    print(json.dumps(result_a, indent=2))
 
    print("\n" + "="*60 + "\n")
 
    # Testing with Bot C (Finance Bro)
    result_c = run_content_engine("Bot_C_FinanceBro")
    print(f"\n[FINAL OUTPUT - Bot C]")
    print(json.dumps(result_c, indent=2))