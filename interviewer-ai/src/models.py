from pydantic import BaseModel, Field


class ResumeProfile(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    claimed_strengths: list[str] = Field(default_factory=list)


class Question(BaseModel):
    question: str
    skill: str
    category: str
    difficulty: str
    reason: str
    resume_evidence: str = ""


class QuestionCandidates(BaseModel):
    follow_up: Question
    deep_dive: Question
    skill_exploration: Question


class AnswerEvaluation(BaseModel):
    score: int = Field(ge=0, le=10)

    technical_correctness: int = Field(
        ge=0,
        le=4,
    )

    relevance: int = Field(
        ge=0,
        le=2,
    )

    depth: int = Field(
        ge=0,
        le=2,
    )

    clarity: int = Field(
        ge=0,
        le=1,
    )

    practical_understanding: int = Field(
        ge=0,
        le=1,
    )

    strengths: list[str] = Field(
        default_factory=list
    )

    gaps: list[str] = Field(
        default_factory=list
    )

    feedback: str = ""

    confidence: float = Field(
        ge=0,
        le=1,
    )


class SemanticAnalysis(BaseModel):
    concepts_demonstrated: list[str] = Field(
        default_factory=list
    )

    concepts_missing: list[str] = Field(
        default_factory=list
    )

    reasoning_quality: str = ""

    evidence_quality: str = ""

    hallucination_or_guessing: bool = False


class FinalEvaluation(BaseModel):
    overall_score: float = Field(
        ge=0,
        le=100,
    )

    recommendation: str

    summary: str

    strengths: list[str] = Field(
        default_factory=list
    )

    gaps: list[str] = Field(
        default_factory=list
    )

    skill_summary: dict[str, str] = Field(
        default_factory=dict
    )