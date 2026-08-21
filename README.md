# Adaptive AI Interviewer----

### ROOMAN AI Challenge | Junior AI Research Associate Selection Round

An adaptive AI-powered technical interviewer that uses a candidate's resume, role requirements, retrieval-augmented generation, structured evaluation, and conditional workflow routing to conduct a personalized interview.

The goal of this project is not simply to generate interview questions. The agent maintains interview state, uses the candidate's background to ground questions, evaluates answers, tracks skill confidence, adapts the next question, and produces a final candidate assessment.

---

## 1. Problem Statement

Traditional interview preparation systems generally follow a fixed pattern:

```text
Question 1
    ↓
Question 2
    ↓
Question 3
    ↓
Question 4
```

This project takes a different approach.

The interviewer adapts based on:

* Candidate resume
* Target role
* Previous answers
* Detected strengths
* Detected gaps
* Current skill confidence
* Interview progress

The result is an interview that behaves more like a structured technical interviewer rather than a simple question generator.

---

## 2. What Does the Agent Do?

### One-line description

> **The agent takes a candidate resume and target role, conducts an adaptive technical interview, evaluates each answer, tracks skills, and produces a final assessment.**

### Input

The system accepts:

* Candidate resume
* Target role / job description
* Candidate answers during the interview

### Output

The system produces:

* Role-specific questions
* Resume-grounded questions
* Follow-up questions when required
* Per-question evaluation
* Skill-level assessment
* Strengths
* Knowledge gaps
* Overall score
* Final recommendation
* Interview history / transcript

---

# 3. ROOMAN Challenge Requirement Mapping

The project was designed against the **Interview Agent** requirements in the ROOMAN AI Challenge.

| Challenge Requirement            | Implementation                                      |
| -------------------------------- | --------------------------------------------------- |
| Generate role-specific questions | Question planning and LLM-based question generation |
| Accept candidate answers         | Interactive interview workflow                      |
| Evaluate candidate answers       | Answer evaluation component                         |
| Support at least 5 questions     | Configurable interview loop                         |
| Produce overall evaluation       | Final evaluation stage                              |
| Identify strengths and gaps      | Skill tracking + final evaluation                   |
| Resume-grounded interview        | Resume parsing + RAG                                |
| Structured agent state           | Interview state                                     |
| Multi-step workflow              | LangGraph                                           |
| Conditional routing              | Interview router                                    |
| Retrieval                        | Embeddings + vector store                           |
| User interface                   | Streamlit UI                                        |
| Per-question scores              | Evaluation results                                  |
| Final recommendation             | Final evaluation                                    |

The implementation intentionally keeps the workflow modular so that each major operation can be inspected independently.

---

# 4. Architecture

At a high level, the system follows:

```text
                    ┌──────────────────────┐
                    │      Candidate       │
                    │       Resume         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Resume Parser     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Chunk + Embeddings  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Vector Store     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    RAG Retrieval      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Question Planner   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Interview Question  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Candidate Answer   │
                    └──────────┬───────────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                     ▼                   ▼
             ┌──────────────┐     ┌──────────────┐
             │    Answer    │     │    Skill     │
             │  Evaluation  │     │   Analysis   │
             └──────┬───────┘     └──────┬───────┘
                    │                    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │     Update State     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Conditional Router   │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             Continue Interview        Finish
                    │                     │
                    │                     ▼
                    │            ┌─────────────────┐
                    │            │ Final Evaluation│
                    │            └────────┬────────┘
                    │                     │
                    └─────────────────────┘
                                          │
                                          ▼
                                         END
```

---

# 5. Agent Workflow

The complete workflow can be understood as:

```text
Input
  ↓
Understand Candidate
  ↓
Understand Role
  ↓
Retrieve Relevant Resume Context
  ↓
Generate Question
  ↓
Receive Answer
  ↓
Evaluate Answer
  ↓
Update Skill Confidence
  ↓
Decide Next Action
  ↓
Ask Follow-up / Increase Difficulty / Move to New Skill
  ↓
Repeat
  ↓
Final Evaluation
```

The important difference from a normal chatbot is that the agent maintains state and makes a decision about what should happen next.

---

# 6. Graph State

The interview workflow maintains a shared state throughout the session.

A simplified representation is:

```python
InterviewState:
    candidate_name
    role
    resume_text
    retrieved_context
    current_question
    current_answer
    question_history
    evaluation_history
    skill_scores
    question_count
    interview_status
    final_evaluation
```

The exact state structure is implemented in the project's `state.py`.

The state allows information from earlier interview steps to influence later decisions.

For example:

```text
Question 1
    ↓
Candidate demonstrates strong Python knowledge
    ↓
Python confidence increases
    ↓
Router selects a more advanced Python question
```

This is what makes the interview adaptive.

---

# 7. Graph Nodes

The workflow is divided into multiple nodes, with each node responsible for a specific task.

## Resume Parser

Responsible for extracting usable text from the candidate resume.

```text
Resume File
    ↓
Text Extraction
    ↓
Clean Resume Text
```

This keeps document handling separate from interview logic.

---

## Embedding / Vector Store

The extracted resume content is converted into searchable representations.

```text
Resume Text
    ↓
Chunks
    ↓
Embeddings
    ↓
Vector Store
```

This allows the system to retrieve relevant parts of the resume instead of sending the complete document for every question.

---

## RAG Retrieval

When the agent needs context, relevant resume information is retrieved.

For example:

```text
Question:
"Tell me about your machine learning experience."

        ↓

Retriever

        ↓

Relevant resume sections:
- ML project
- Python experience
- Model evaluation
- Previous work
```

The retrieved information is then supplied to the question-generation or evaluation stage.

---

## Question Planner

The planner determines what type of question should be asked next.

It can consider:

* Target role
* Required skills
* Resume evidence
* Previous questions
* Previous answers
* Current skill confidence
* Interview progress

The goal is to avoid repeatedly asking the same generic questions.

---

## Interviewer

The interviewer presents the generated question to the candidate and collects the answer.

This forms the interaction loop:

```text
Agent Question
      ↓
Candidate Answer
      ↓
Evaluation
      ↓
Next Question
```

---

## Answer Evaluator

The answer evaluator assesses the candidate's response.

Depending on the question, evaluation can consider:

* Correctness
* Technical depth
* Relevance
* Clarity
* Reasoning
* Practical understanding

The evaluation is stored in the interview state.

---

## Skill Tracker

The agent tracks evidence about individual skills.

For example:

```text
Python
Confidence: High

SQL
Confidence: Medium

Machine Learning
Confidence: High

System Design
Confidence: Low
```

This information can influence subsequent question selection.

---

## Router

The router decides what should happen next.

Possible outcomes include:

```text
Continue interview
        ↓
Ask follow-up
        ↓
Increase difficulty
        ↓
Move to another skill
        ↓
Finish interview
```

This is one of the main components that makes the application agentic.

---

## Final Evaluator

Once the interview is complete, the final evaluator combines the accumulated evidence.

The final result includes:

* Overall assessment
* Technical strengths
* Weak areas
* Skill confidence
* Interview performance
* Recommendation

---

# 8. Sequential Edges

Some workflow steps always happen in sequence.

For example:

```text
Resume Parser
      ↓
Embedding
      ↓
Vector Store
      ↓
RAG Retrieval
      ↓
Question Planner
```

Another sequential section is:

```text
Candidate Answer
      ↓
Evaluation
      ↓
State Update
```

These edges represent deterministic progression through the workflow.

---

# 9. Parallel Workflow

Some pieces of analysis are independent of each other.

For example, after a candidate provides an answer:

```text
                 Candidate Answer
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
      Answer Evaluation      Skill Analysis
             │                     │
             └──────────┬──────────┘
                        ▼
                   State Update
```

The purpose of separating these operations is to keep responsibilities independent.

Where the implementation executes independent operations concurrently, this can also reduce unnecessary waiting time.

The important design principle is that answer quality and skill evidence are different pieces of information and should not be treated as one opaque score.

---

# 10. Conditional Workflow

The interview does not always follow the same path.

After evaluation, the router determines what should happen next.

Conceptually:

```text
                       Evaluation
                            │
                    ┌───────┴───────┐
                    │               │
             Strong Evidence    Weak / Unclear
                    │               │
                    ▼               ▼
             Increase Depth     Ask Follow-up
                    │               │
                    └───────┬───────┘
                            │
                            ▼
                       Next Question
```

Another condition is interview completion:

```text
              Interview State
                    │
              ┌─────┴─────┐
              │           │
         Questions < N  Questions >= N
              │           │
              ▼           ▼
         Continue       Finish
              │           │
              │           ▼
              │     Final Evaluation
              │
              └──────► Next Question
```

The exact routing logic is implemented in the project's router/graph components.

---

# 11. Why LangGraph?

LangGraph was selected because the interview naturally behaves like a stateful graph.

A normal sequential function would make the workflow harder to reason about as the number of decisions increases.

With a graph:

```text
State
  ↓
Node
  ↓
State Update
  ↓
Conditional Decision
  ↓
Next Node
```

each step has a clear responsibility.

This also makes it easier to add:

* More question types
* More evaluation stages
* Additional routing decisions
* Human review
* More tools

without putting everything into one large function.

---

# 12. Resume-Grounded RAG

A key feature of the project is grounding the interview in the candidate's resume.

Instead of asking generic questions such as:

> "Tell me about yourself."

the agent can use resume evidence to ask more relevant questions.

For example:

```text
Resume:
"Developed a recommendation system using Python
and collaborative filtering."

        ↓

Retrieved Context

        ↓

Interview Question:
"Can you explain how you approached the recommendation
system and why you selected collaborative filtering?"
```

This creates a more personalized interview.

---

# 13. Why RAG?

Sending the complete resume to the model for every question is inefficient and becomes less practical as documents grow.

The retrieval pipeline is:

```text
Resume
  ↓
Text extraction
  ↓
Chunking
  ↓
Embeddings
  ↓
Vector store
  ↓
Similarity retrieval
  ↓
Relevant context
  ↓
LLM
```

The model receives the context most relevant to the current interview step.

---

# 14. Question Adaptation

The interviewer is designed to adapt rather than ask a fixed list.

For example:

```text
Candidate demonstrates strong Python fundamentals
                    ↓
              Increase difficulty
                    ↓
Ask advanced Python question
```

Whereas:

```text
Candidate struggles with SQL joins
                    ↓
              Reduce difficulty
                    ↓
Ask a clarification / foundational question
```

The purpose is not to make the interview unnecessarily difficult.

The purpose is to collect better evidence about the candidate's actual skill level.

---

# 15. Scoring Approach

The project uses the LLM for semantic evaluation while maintaining structured application-level state.

A response can be evaluated on factors such as:

```text
Technical correctness
        +
Relevance
        +
Depth
        +
Reasoning
        +
Clarity
```

The individual evaluation is stored and contributes to the final assessment.

The final score should therefore be treated as an evaluation signal rather than an objective measurement of a candidate's real-world ability.

---

# 16. Avoiding Hallucinated Candidate Information

The interviewer should distinguish between:

```text
Evidence found in resume
```

and:

```text
Information not found in resume
```

For example:

### Incorrect

> The candidate has no AWS experience.

### Better

> AWS experience was not identified in the provided resume.

The system should not invent candidate experience simply because the model expects it.

This is particularly important in recruitment-related applications.

---

# 17. Example Interview

### Target Role

```text
Junior Machine Learning Engineer
```

### Candidate Background

```text
Python developer with experience in machine learning,
SQL and data processing.

Projects include a recommendation system and
a predictive analytics pipeline.
```

---

## Question 1

**Interviewer:**

> Explain one machine learning project you worked on and your specific contribution.

**Candidate:**

> I built a recommendation system using Python and collaborative filtering. I worked on data preprocessing, feature preparation and evaluating the model.

**Evaluation:**

```text
Score: 8/10

Strengths:
- Relevant project experience
- Clear technical contribution
- Understands the basic workflow

Gap:
- Could explain model selection in more depth
```

---

## Question 2

The system detects machine learning experience and asks a deeper question.

**Interviewer:**

> Why did you choose collaborative filtering for that recommendation system?

**Candidate:**

> The dataset contained user-item interactions, so collaborative filtering allowed us to use similarities between users and items rather than relying only on manually defined product features.

**Evaluation:**

```text
Score: 9/10

Strengths:
- Good reasoning
- Understands the underlying approach
- Connects method to dataset characteristics
```

---

## Question 3

**Interviewer:**

> How would you handle missing values in a dataset before training a model?

**Evaluation:**

```text
Score: 7/10
```

---

## Question 4

**Interviewer:**

> How would you identify whether your model is overfitting?

**Evaluation:**

```text
Score: 8/10
```

---

## Question 5

**Interviewer:**

> Suppose your model performs well during training but poorly on unseen data. How would you investigate the problem?

**Evaluation:**

```text
Score: 8/10
```

---

# 18. Example Final Evaluation

```text
Candidate: Example Candidate
Role: Junior Machine Learning Engineer

Overall Score: 8.0 / 10

Technical Strengths:
- Strong Python fundamentals
- Good understanding of machine learning concepts
- Relevant project experience
- Good reasoning about model selection

Areas for Improvement:
- More depth in model deployment
- Advanced data engineering concepts
- Production monitoring experience

Skill Assessment:

Python              High
Machine Learning    High
SQL                 Medium
Data Processing     High
Deployment          Medium

Recommendation:

Proceed to the next interview round.

The candidate demonstrated strong fundamentals and
relevant practical experience. The main gaps are in
production-level deployment and advanced engineering.
```

---

# 19. UI

The project includes a user interface for running the interview without manually interacting with the Python workflow.

The general UI flow is:

```text
┌──────────────────────────────────────────┐
│           Adaptive AI Interviewer        │
├──────────────────────────────────────────┤
│                                          │
│ Candidate Resume                         │
│ [ Upload Resume ]                        │
│                                          │
│ Target Role                              │
│ [ Python / ML Engineer ]                 │
│                                          │
│ Number of Questions                      │
│ [ 5 ]                                    │
│                                          │
│          [ Start Interview ]             │
│                                          │
├──────────────────────────────────────────┤
│ Interview                                │
│                                          │
│ Question:                                │
│ How would you handle overfitting?        │
│                                          │
│ Your Answer:                             │
│ ┌──────────────────────────────────────┐ │
│ │                                      │ │
│ └──────────────────────────────────────┘ │
│                                          │
│              [ Submit Answer ]           │
│                                          │
└──────────────────────────────────────────┘
```

The UI is intentionally lightweight.

The goal of the challenge was to demonstrate the agent workflow rather than spend most of the available time building a complex frontend.

---

# 20. Technology Stack

| Component         | Technology                     |
| ----------------- | ------------------------------ |
| Language          | Python                         |
| Agent workflow    | LangGraph                      |
| LLM               | Configurable LLM API           |
| Resume processing | Python document parsing        |
| Embeddings        | Embedding model                |
| Retrieval         | Vector store                   |
| RAG               | Retrieval-Augmented Generation |
| UI                | Streamlit                      |
| Testing           | Pytest                         |
| Configuration     | Environment variables          |

---

# 21. Project Structure

```text
InterviewAI/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── interviewer-ai/
│   │
│   ├── app.py
│   │
│   ├── src/
│   │   ├── embeddings.py
│   │   ├── evaluator.py
│   │   ├── graph.py
│   │   ├── interview.py
│   │   ├── knowledge.py
│   │   ├── llm.py
│   │   ├── models.py
│   │   ├── planner.py
│   │   ├── prompts.py
│   │   ├── rag.py
│   │   ├── resume.py
│   │   ├── resume_parser.py
│   │   ├── router.py
│   │   ├── state.py
│   │   └── vector_store.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_router.py
│   │   ├── test_evaluator.py
│   │   ├── test_resume_parser.py
│   │   └── test_state.py
│   │
│   └── data/
│       └── sample_resume.pdf
│
└── screenshots/
    ├── ui.png
    ├── interview.png
    ├── evaluation.png
    └── workflow.png
```

Update this section if your actual repository structure differs.

---

# 22. Installation

## Clone the repository

```bash
git clone https://github.com/srishtipatgar6/InterviewAI.git
cd InterviewAI
```

Move into the application directory if required:

```bash
cd interviewer-ai
```

---

## Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The virtual environment is intentionally not committed to GitHub.

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# 23. Environment Variables

Create a local `.env` file.

Example:

```env
OPENAI_API_KEY=your_api_key_here
```

Never commit the real `.env` file or API keys to GitHub.

A `.env.example` file is provided as a reference.

---

# 24. Running the Application

If the application uses Streamlit:

```bash
streamlit run app.py
```

The application can then be opened in the browser.

---

# 25. Testing

The project includes tests for important application-level components.

Run:

```bash
pytest -v
```

Tests focus on deterministic parts of the system such as:

* Resume parsing
* Interview state
* Evaluation logic
* Routing logic

External LLM responses are not tested by comparing exact generated text because model responses can vary.

Instead, the application logic around the model is tested separately.

Example:

```text
tests/
├── test_router.py
├── test_evaluator.py
├── test_resume_parser.py
└── test_state.py
```

---

# 26. Sample Data

The repository contains sample input data so the project can be tested without creating everything from scratch.

The sample includes:

* Candidate resume
* Target role
* Example interview session
* Example evaluation

This allows a reviewer to reproduce the basic workflow.

---

# 27. Design Decisions

## Why use an LLM?

Interviewing requires understanding natural language.

A candidate may demonstrate the same concept using very different wording.

For example:

```text
Candidate:
"I used pandas to clean and transform the dataset."

Role requirement:
"Experience with data preprocessing."
```

Simple keyword matching may miss this relationship.

An LLM can reason about the semantic connection.

---

## Why use RAG?

RAG allows the interviewer to ground questions in the candidate's actual resume.

This reduces the need to place the entire resume into every prompt and makes it easier to retrieve relevant evidence.

---

## Why use a graph?

The interview is stateful.

The next question depends on what happened previously.

A graph represents this naturally:

```text
Current State
     ↓
Evaluate
     ↓
Decide
     ↓
Update State
     ↓
Next Action
```

---

## Why use deterministic routing?

The LLM is useful for understanding and evaluating natural language, but workflow control should remain predictable wherever possible.

Therefore:

```text
LLM
 ↓
Evaluation
 ↓
Structured result
 ↓
Application logic
 ↓
Router
```

is preferable to asking the LLM to control the entire application without constraints.

---

# 28. Tradeoffs

This project was developed under the 24-hour challenge constraint.

Some design choices were therefore intentionally conservative.

### 1. Lightweight UI

Streamlit was chosen instead of building a full frontend.

This allowed more time to be spent on the agent workflow.

### 2. LLM dependency

The quality of semantic question generation and answer evaluation depends on the selected model.

A stronger model may improve reasoning but can increase cost and latency.

### 3. Local vector retrieval

A lightweight vector store is sufficient for the challenge.

A production application could use a managed vector database.

### 4. Limited persistence

The challenge focuses on the interview agent rather than long-term candidate management.

A production system would require a proper database and authentication layer.

### 5. Human-in-the-loop

The final recommendation should support a recruiter or interviewer rather than replace human judgment.

---

# 29. Limitations

This is a challenge project and should not be treated as a production recruitment platform.

Current limitations include:

* LLM responses can vary.
* Resume parsing can be affected by unusual document formatting.
* A resume does not necessarily contain all of a candidate's skills.
* Interview scores are approximate evaluation signals.
* Semantic similarity does not guarantee actual job performance.
* Different roles may require different scoring criteria.
* The system should not infer sensitive personal characteristics.
* Final hiring decisions should remain with qualified human reviewers.

---

# 30. Responsible Use

The system is intended as an interview-assistance tool.

It should not be used to make automated decisions based on protected or sensitive characteristics.

The interviewer should evaluate only job-relevant information such as:

* Technical knowledge
* Relevant experience
* Problem-solving ability
* Communication of technical concepts
* Role-specific skills

The system should not infer characteristics that are unrelated to job performance.

---

# 31. What I Would Improve With More Time

If more development time were available, I would focus on:

### Better evaluation

Create a human-labeled benchmark containing interview questions, candidate answers, and expected evaluation ranges.

### Better retrieval

Experiment with hybrid retrieval:

```text
Keyword Search
      +
Vector Search
      +
LLM Reranking
      ↓
Relevant Context
```

### Better interview planning

Add explicit skill coverage planning so that the interviewer systematically covers the required competencies.

### Better observability

Add logs and traces for:

* Retrieved context
* Generated questions
* Router decisions
* Evaluation results
* State transitions

### Persistent candidate sessions

Store interview sessions in a database so that interviews can be resumed.

### Human feedback

Allow an interviewer to correct an evaluation and use that feedback to improve future evaluations.

### Model evaluation

Compare different models for:

* Question quality
* Evaluation consistency
* Latency
* Cost
* Hallucination rate

---

# 32. Why This Is an Agent

The core of the project is not simply:

```text
User → LLM → Response
```

The workflow is:

```text
Input
  ↓
State
  ↓
Retrieve Context
  ↓
Reason
  ↓
Generate Question
  ↓
Receive Answer
  ↓
Evaluate
  ↓
Update State
  ↓
Make Decision
  ↓
Take Next Action
  ↓
Repeat
  ↓
Final Result
```

The system therefore has the important characteristics of an agent:

* It maintains state.
* It uses external data.
* It retrieves relevant context.
* It evaluates information.
* It makes conditional decisions.
* It changes its next action based on previous results.
* It produces a final structured outcome.

---

# 33. 24-Hour Challenge Scope

The project was intentionally scoped around the core requirements of the ROOMAN AI Challenge.

The priority was:

```text
1. Working end-to-end interview
        ↓
2. Resume grounding
        ↓
3. Adaptive questioning
        ↓
4. Answer evaluation
        ↓
5. Conditional workflow
        ↓
6. UI
        ↓
7. Testing
        ↓
8. Documentation
```

The objective was not to build a complete enterprise recruitment platform within 24 hours.

The objective was to demonstrate a working AI agent with a clear architecture and explainable design decisions.

---

# 34. Final Demo Flow

A reviewer can reproduce the complete workflow as follows:

```text
1. Start the application
        ↓
2. Upload a sample resume
        ↓
3. Select a target role
        ↓
4. Start the interview
        ↓
5. Answer at least 5 questions
        ↓
6. Observe adaptive questions
        ↓
7. Observe per-answer evaluation
        ↓
8. Observe skill tracking
        ↓
9. Complete the interview
        ↓
10. Review final evaluation
```

---

# 35. Repository

GitHub:

https://github.com/srishtipatgar6/InterviewAI

---

# 36. Author

**Srishti Patgar**

Built for:

**ROOMAN Technologies Pvt. Ltd.**

**Junior AI Research Associate — 24-Hour AI Agent Challenge**

---

## Final Note

This project was built with a simple principle:

> **An AI interviewer should not only ask questions. It should remember what happened, understand the evidence, decide what to ask next, and explain its final assessment.**

That principle shaped the state management, retrieval system, evaluation pipeline, and conditional workflow used in this project.
