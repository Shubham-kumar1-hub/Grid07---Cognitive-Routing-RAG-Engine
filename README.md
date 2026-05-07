# Grid07 - AI Cognitive Routing & RAG Engine

A Python-based AI system built for the Grid07 internship assignment. It handles smart bot routing, autonomous post generation, and context-aware debate replies - all using free, local tools.

**Stack:** Python 3.12 · LangGraph · FAISS · BAAI/bge-small-en-v1.5 · Groq (llama3-8b)

---

## Project Structure

```
grid07/
├── phase1.py          # Bot router using FAISS + HuggingFace embeddings
├── phase2.py          # Autonomous post engine built with LangGraph
├── phase3.py          # RAG combat engine with prompt injection defense
├── requirements.txt   # Dependencies
├── .env.example       # API key template
├── execution_logs.md  # Real console output from all three phases
└── README.md
```

---

## Setup

```bash
# Clone and enter the project
git clone https://github.com/your-username/grid07-ai-engine.git
cd grid07-ai-engine

# Create a virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
cp .env.example .env
# Open .env and paste your GROQ_API_KEY
```

Free Groq API key: https://console.groq.com

---

## Running the Phases

```bash
python phase1.py   # Persona router
python phase2.py   # Autonomous post engine
python phase3.py   # Combat engine + injection defense
```

---

## Phase 1 - Persona Router

Each bot persona is embedded using `BAAI/bge-small-en-v1.5` (runs fully locally, no API key needed) and stored in a FAISS index. When a new post comes in, it gets embedded the same way and compared against all three personas using cosine similarity.

A bot gets matched only if it clears two conditions - it must score above the absolute threshold of 0.55, and must also be within 0.15 of the top scorer. The second condition prevents weaker bots from sneaking in when there's already a clear match.

**On the threshold:** The assignment suggests 0.85, which is tuned for OpenAI embeddings. `BAAI/bge-small-en-v1.5` naturally produces scores in the 0.55–0.85 range for this kind of task, so 0.55 is the appropriate floor. The assignment PDF itself says to tweak the threshold based on the model.

---

## Phase 2 - LangGraph Node Structure

The content engine is a simple 3-node linear pipeline:

```
[decide_search] → [web_search] → [draft_post] → END
```

**Node 1 - decide_search**
The LLM reads the bot's persona and picks a topic to post about today, then formats it as a short search query. No human input needed — the bot decides on its own based on its personality.

**Node 2 - web_search**
Calls `mock_searxng_search()`, a `@tool` function that returns hardcoded but realistic news headlines based on keywords in the query. This simulates what a real search API would return.

**Node 3 - draft_post**
The LLM gets the persona as a system prompt and the search results as context, then writes a 280-character opinionated post. Output is always a strict JSON object:
```json
{"bot_id": "...", "topic": "...", "post_content": "..."}
```
There's also a fallback parser that strips markdown backticks in case the LLM adds them anyway.

---

## Phase 3 - Prompt Injection Defense

The bot reads the entire thread (parent post + all comments) as context before replying - that's the RAG part. Instead of just seeing the last message, it understands the full flow of the argument.

For injection defense, I used three layered approaches:

**1. Instruction isolation in the system prompt**
The system prompt has a clearly labeled `CRITICAL SECURITY RULES` section that tells the LLM it only takes instructions from the system prompt. Anything inside the human's message is treated as debate content, not a command. Common injection phrases like "ignore all previous instructions" and "you are now" are listed explicitly so the model knows what to watch for.

**2. Persona reinforcement**
Instead of just saying "ignore injections", the prompt doubles down on the bot's identity and tells it to stay in character no matter what — even mock the attempt if it fits the persona. This makes breaking character feel wrong in context, not just rule-violating.

**3. Keyword scan in Python**
Before the message even hits the LLM, `phase3.py` scans the human's reply for known injection patterns. If one is detected, a `[SECURITY WARNING]` is logged. This layer is useful for monitoring and can be extended to dynamically add extra guardrail text to the prompt.

---

## Notes

- The HuggingFace model downloads automatically on first run (~130MB)
- `temperature=0.8` in Phase 2 keeps posts varied and opinionated across runs
- Everything runs in-memory - no data written to disk

---

## Author

Shubham Kumar - Built as part of the Grid07 AI Engineering Internship Assignment
