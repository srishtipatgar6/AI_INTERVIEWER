import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


DEFAULT_MODEL = "llama-3.3-70b-versatile"


# ============================================================
# GROQ
# ============================================================

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing.\n\n"
            "Create a .env file in the project root:\n\n"
            "GROQ_API_KEY=your_groq_api_key"
        )

    model_name = os.getenv(
        "GROQ_MODEL",
        DEFAULT_MODEL
    )

    return ChatGroq(
        model=model_name,
        temperature=0.15,
        api_key=api_key,
    )


# ============================================================
# BASIC LLM CALL
# ============================================================

def call_llm(prompt: str) -> str:

    response = get_llm().invoke(prompt)

    content = response.content

    if isinstance(content, str):
        return content

    return str(content)


# ============================================================
# JSON PARSER
# ============================================================

def parse_json(text: str) -> Dict[str, Any]:

    if not text:
        raise ValueError(
            "Empty response from Groq."
        )

    text = text.strip()

    # Remove markdown fences
    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace(
        "```",
        ""
    ).strip()

    # Try complete JSON first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        candidate = text[
            start:end + 1
        ]

        try:
            return json.loads(candidate)

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Groq returned invalid JSON:\n\n"
                + candidate
            ) from exc

    raise ValueError(
        "Could not find JSON in Groq response:\n\n"
        + text
    )


# ============================================================
# RESUME PROFILE
# ============================================================

def extract_candidate_profile(
    resume_text: str,
    role: str,
    declared_skills: List[str],
) -> Dict[str, Any]:

    prompt = f"""
You are an expert technical recruiter.

Build a structured interview profile from the candidate's resume.

TARGET ROLE:
{role}

CANDIDATE DECLARED SKILLS:
{", ".join(declared_skills)}

RESUME:
{resume_text}

IMPORTANT:

The resume is the source of truth.

Do not invent:
- technologies
- projects
- companies
- certifications
- responsibilities
- experience

Return ONLY valid JSON.

Use this exact structure:

{{
    "summary": "short candidate summary",
    "skills": [
        "skill explicitly supported by resume"
    ],
    "technologies": [
        "technology explicitly supported by resume"
    ],
    "projects": [
        {{
            "name": "project name",
            "technologies": [],
            "description": "short description"
        }}
    ],
    "experience": [
        {{
            "company": "company name",
            "role": "role",
            "technologies": [],
            "responsibilities": []
        }}
    ],
    "certifications": [],
    "interview_topics": [
        {{
            "topic": "specific resume-supported topic",
            "skill": "related skill",
            "evidence": "short resume evidence"
        }}
    ]
}}

Create interview_topics only from actual resume evidence.
"""

    result = parse_json(
        call_llm(prompt)
    )

    return result


# ============================================================
# FIRST QUESTION
# ============================================================

def generate_first_question(
    role: str,
    skills: List[str],
    profile: Dict[str, Any],
    resume_context: str,
) -> Dict[str, Any]:

    prompt = f"""
You are conducting a professional technical interview.

TARGET ROLE:
{role}

DECLARED SKILLS:
{", ".join(skills)}

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

RELEVANT RESUME CONTEXT:
{resume_context}

Generate the FIRST interview question.

CRITICAL QUESTION RULES:

1. Ask exactly ONE question.

2. Maximum 25 words.

3. Prefer 10-20 words.

4. Test ONE concept only.

5. The question must be answerable in about 30-60 seconds.

6. The question MUST be grounded in the resume.

7. Do not introduce technologies absent from the resume.

8. Prefer a specific project, technology, responsibility,
   or skill appearing in the resume.

9. Do not ask:
   "Describe your entire project."

10. Do not ask multiple things using "and".

11. Do not ask for an entire pipeline.

12. Do not ask unrelated theoretical questions.

Return ONLY JSON:

{{
    "question": "short question",
    "skill": "one resume skill",
    "topic": "one specific topic",
    "difficulty": "easy|medium"
}}
"""

    return parse_json(
        call_llm(prompt)
    )


# ============================================================
# ANSWER EVALUATION
# ============================================================

def evaluate_answer(
    role: str,
    skills: List[str],
    question: str,
    answer: str,
    resume_context: str,
    difficulty: str,
    previous_scores: List[float],
) -> Dict[str, Any]:

    prompt = f"""
You are an expert technical interviewer.

Evaluate the candidate's answer.

ROLE:
{role}

DECLARED SKILLS:
{", ".join(skills)}

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

RESUME CONTEXT:
{resume_context}

CURRENT DIFFICULTY:
{difficulty}

PREVIOUS SCORES:
{previous_scores}

Evaluate ONLY what the candidate actually demonstrated.

Do not punish concise answers if they correctly answer the question.

Score from 0 to 10.

0-2 = incorrect / no understanding
3-4 = weak
5-6 = basic understanding
7-8 = good understanding
9-10 = excellent depth

Determine the next interview strategy:

"easier"
    if the candidate struggled.

"follow_up"
    if clarification is needed.

"deeper"
    if the candidate demonstrated strong understanding.

"new_topic"
    if enough evidence exists for this topic.

"finish"
    only if enough interview evidence has been collected.

Return ONLY JSON:

{{
    "score": 0,
    "correctness": "weak|partial|strong",
    "knowledge_level": "beginner|intermediate|advanced",
    "feedback": "short professional feedback",
    "strength": "what the candidate demonstrated",
    "gap": "what was missing",
    "next_strategy": "easier|follow_up|deeper|new_topic|finish",
    "recommended_difficulty": "easy|medium|hard"
}}
"""

    return parse_json(
        call_llm(prompt)
    )


# ============================================================
# NEXT QUESTION
# ============================================================

def generate_next_question(
    role: str,
    skills: List[str],
    candidate_profile: Dict[str, Any],
    resume_context: str,
    previous_question: str,
    previous_answer: str,
    evaluation: Dict[str, Any],
    asked_questions: List[str],
    current_topic: str,
    difficulty: str,
    available_topics: List[Any],
) -> Dict[str, Any]:

    prompt = f"""
You are an adaptive technical interviewer.

TARGET ROLE:
{role}

DECLARED SKILLS:
{", ".join(skills)}

CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

CURRENT RESUME CONTEXT:
{resume_context}

CURRENT TOPIC:
{current_topic}

PREVIOUS QUESTION:
{previous_question}

PREVIOUS ANSWER:
{previous_answer}

ANSWER EVALUATION:
{json.dumps(evaluation, indent=2)}

REQUESTED DIFFICULTY:
{difficulty}

AVAILABLE RESUME TOPICS:
{json.dumps(available_topics, indent=2)}

QUESTIONS ALREADY ASKED:
{json.dumps(asked_questions, indent=2)}

QUESTION GENERATION RULES:

1. Generate exactly ONE question.

2. Maximum 25 words.

3. Prefer 10-20 words.

4. Test ONE concept only.

5. The candidate should answer in approximately 30-60 seconds.

6. The resume is the source of truth.

7. NEVER invent experience.

8. NEVER introduce a technology not supported by the resume.

9. NEVER repeat an existing question.

10. Do not combine multiple questions.

11. Do not ask for an entire solution.

12. If the previous answer was WEAK:
    ask an easier question about the same concept.

13. If the previous answer was PARTIAL:
    ask a focused clarification question.

14. If the previous answer was STRONG:
    ask a deeper question about the same topic.

15. If the candidate has demonstrated enough knowledge
    of the current topic:
    move to another topic explicitly present in the resume.

16. The target role may influence framing,
    but resume evidence must support the topic.

17. Keep questions precise and professional.

QUESTION RULES:

1. Ask EXACTLY ONE question.
2. Keep it short: maximum 2 sentences.
3. Prefer 10-25 words.
4. Never ask a multi-part question.
5. Never use:
   - "Explain the steps, libraries, and evaluation..."
   - "Describe X, Y, and Z..."
   - "How would you design..., implement..., optimize..., and evaluate..."
6. Ask one focused question about ONE skill or ONE resume experience.
7. Ground the question in the uploaded resume.
8. If the candidate mentioned a specific project, technology,
   certification, job, or achievement, you may ask a focused
   follow-up about it.
9. Do not invent experience that is not present in the resume.
10. Do not ask generic textbook questions unless that concept
    is explicitly supported by the candidate's resume or skills.
11. If the candidate answered strongly, increase difficulty slightly.
12. If the candidate answered weakly, ask a simpler diagnostic
    question before increasing difficulty.
13. Avoid repeating previous questions.
14. The candidate should be able to answer the question in
    approximately 30-60 seconds.

EXAMPLES OF GOOD QUESTIONS:

"Why did you choose Pandas for this feature extraction task?"

"How did you handle missing values in this dataset?"

"What did your PL/SQL trigger validate?"

"Why was this SQL query slow?"

"How did you evaluate the model?"

EXAMPLES OF BAD QUESTIONS:

"Describe your entire machine learning pipeline."

"Explain your project, libraries, challenges, deployment, and results."

"How would you design the entire system?"

Return ONLY JSON:

{{
    "question": "short single-concept question",
    "skill": "resume-supported skill",
    "topic": "specific resume-supported topic",
    "difficulty": "easy|medium|hard"
}}
"""

    return parse_json(
        call_llm(prompt)
    )


# ============================================================
# FINAL EVALUATION
# ============================================================

def generate_final_evaluation(
    candidate_name: str,
    role: str,
    skills: List[str],
    profile: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    compact_history = []

    for item in history:

        compact_history.append(
            {
                "question": item.get(
                    "question",
                    ""
                ),
                "answer": item.get(
                    "answer",
                    ""
                ),
                "skill": item.get(
                    "skill",
                    ""
                ),
                "topic": item.get(
                    "topic",
                    ""
                ),
                "score": item.get(
                    "score",
                    0
                ),
                "evaluation": item.get(
                    "evaluation",
                    {}
                ),
            }
        )

    prompt = f"""
You are a senior technical interviewer.

Prepare the final interview evaluation.

CANDIDATE:
{candidate_name}

TARGET ROLE:
{role}

DECLARED SKILLS:
{", ".join(skills)}

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

INTERVIEW:
{json.dumps(compact_history, indent=2)}

Evaluate only evidence demonstrated during this interview.

Do not infer skills that were not demonstrated.

Return ONLY JSON:

{{
    "candidate_name": "{candidate_name}",
    "role": "{role}",
    "overall_score": 0,
    "technical_assessment": "professional summary",
    "strengths": [
        "strength"
    ],
    "knowledge_gaps": [
        "gap"
    ],
    "skills_assessment": [
        {{
            "skill": "skill",
            "score": 0,
            "remark": "assessment based on interview evidence"
        }}
    ],
    "recommendation": "Strong Hire|Hire|Consider|Not Recommended",
    "final_remarks": "concise final interviewer remarks"
}}

overall_score must be from 0 to 10.

Be evidence-based and professional.
"""

    return parse_json(
        call_llm(prompt)
    )