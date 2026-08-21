# Adaptive AI Interviewer

An AI-powered technical interviewer that conducts
personalized interviews using the candidate's resume,
role, skills, previous answers and adaptive skill confidence.

## Architecture

Candidate Resume
        |
        v
Resume Parser
        |
        v
Chunking + Embeddings
        |
        v
FAISS Resume Vector Store
        |
        +----------------------+
                               |
Interview Knowledge ---------->|
                               v
                         RAG Retrieval
                               |
                               v
                         Groq LLM
                               |
                    +----------+----------+
                    |          |          |
                Follow-up  Deep Dive  Skill Explore
                    |          |          |
                    +----------+----------+
                               |
                               v
                        Question Selector
                               |
                               v
                        Candidate Answer
                               |
                    +----------+----------+
                    |                     |
              Technical Judge       Semantic Analysis
                    |                     |
                    +----------+----------+
                               |
                               v
                         Skill Update
                               |
                               v
                       Conditional Edge
                         /          \
                        /            \
                   Continue         Finish
                      |
                      v
                 Next Question

## Features

- Resume-grounded interview
- RAG over candidate resume
- Role-specific questions
- Skill-specific questions
- Adaptive difficulty
- Follow-up questions
- Deep-dive questions
- Cross-skill exploration
- Parallel retrieval
- Parallel answer evaluation
- Conditional LangGraph routing
- Per-question scoring
- Skill confidence tracking
- Resume claim verification
- Full interview transcript
- Final recommendation
- Candidate can end interview at any time

## Tech Stack

- Python
- Groq
- LangGraph
- LangChain
- FAISS
- HuggingFace Sentence Transformers
- Streamlit

## Installation

```bash
python -m venv .venv