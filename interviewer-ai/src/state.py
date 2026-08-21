from typing import TypedDict, Any


class InterviewState(TypedDict, total=False):

    name: str
    target_role: str
    target_skills: list[str]

    resume_text: str
    resume_profile: dict[str, Any]

    min_questions: int
    max_questions: int
    question_count: int

    current_question: dict[str, Any]
    current_answer: str

    questions: list[dict[str, Any]]
    transcript: list[dict[str, Any]]

    current_evaluation: dict[str, Any]
    current_semantic_analysis: dict[str, Any]

    evaluations: list[dict[str, Any]]

    skill_scores: dict[str, float]
    skill_confidence: dict[str, float]

    covered_skills: list[str]
    weak_areas: list[str]
    strong_areas: list[str]

    resume_claims_tested: list[str]
    resume_claims_verified: list[str]

    retrieved_resume_context: list[str]
    retrieved_knowledge_context: list[str]

    retrieval_metadata: list[dict[str, Any]]

    next_strategy: str
    next_skill: str
    next_difficulty: str
    selection_reason: str

    candidate_ended: bool
    interview_completed: bool
    completion_reason: str

    final_evaluation: dict[str, Any]