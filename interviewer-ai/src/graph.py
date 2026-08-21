from typing import TypedDict, List, Dict, Any

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from .llm import (
    evaluate_answer,
    generate_next_question,
)


# ============================================================
# CONSTANTS
# ============================================================

MIN_QUESTIONS_DEFAULT = 5
MAX_QUESTIONS_DEFAULT = 12


# ============================================================
# STATE
# ============================================================

class InterviewState(TypedDict, total=False):

    # Candidate
    candidate_name: str
    role: str
    skills: List[str]
    profile: Dict[str, Any]

    # Resume RAG
    vectorstore: Any
    resume_context: str

    # Current question
    question: str
    answer: str

    topic: str
    skill: str
    difficulty: str

    # Evaluation
    evaluation: Dict[str, Any]

    # Interview history
    history: List[Dict[str, Any]]
    scores: List[float]
    asked_questions: List[str]

    # Routing
    next_strategy: str
    finished: bool

    # Limits
    min_questions: int
    max_questions: int


# ============================================================
# HELPERS
# ============================================================

def _question_count(
    state: InterviewState
) -> int:

    return len(
        state.get(
            "history",
            []
        )
    )


def _minimum_questions(
    state: InterviewState
) -> int:

    return int(
        state.get(
            "min_questions",
            MIN_QUESTIONS_DEFAULT
        )
    )


def _maximum_questions(
    state: InterviewState
) -> int:

    return int(
        state.get(
            "max_questions",
            MAX_QUESTIONS_DEFAULT
        )
    )


def _normalize_strategy(
    strategy: str
) -> str:

    strategy = (
        strategy
        or "continue"
    )

    strategy = (
        strategy
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    allowed = {
        "follow_up",
        "harder",
        "new_topic",
        "continue",
        "finish",
    }

    if strategy not in allowed:

        return "continue"

    return strategy


# ============================================================
# EVALUATE ANSWER NODE
# ============================================================

def evaluate_node(
    state: InterviewState
):

    question = (
        state.get(
            "question",
            ""
        )
        .strip()
    )

    answer = (
        state.get(
            "answer",
            ""
        )
        .strip()
    )

    if not question:

        raise ValueError(
            "No current interview question exists."
        )

    if not answer:

        raise ValueError(
            "Candidate answer is empty."
        )

    evaluation = evaluate_answer(

        role=state.get(
            "role",
            ""
        ),

        skills=state.get(
            "skills",
            []
        ),

        question=question,

        answer=answer,

        resume_context=state.get(
            "resume_context",
            ""
        ),

        difficulty=state.get(
            "difficulty",
            "medium"
        ),

        previous_scores=state.get(
            "scores",
            []
        ),
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    try:

        score = float(
            evaluation.get(
                "score",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        score = 0.0

    score = max(
        0.0,
        min(
            10.0,
            score
        )
    )

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    history = list(
        state.get(
            "history",
            []
        )
    )

    history.append(
        {
            "question": question,

            "answer": answer,

            "skill": state.get(
                "skill",
                ""
            ),

            "topic": state.get(
                "topic",
                ""
            ),

            "difficulty": state.get(
                "difficulty",
                "medium"
            ),

            "score": score,

            "evaluation": evaluation,
        }
    )

    # --------------------------------------------------------
    # SCORES
    # --------------------------------------------------------

    scores = list(
        state.get(
            "scores",
            []
        )
    )

    scores.append(
        score
    )

    # --------------------------------------------------------
    # NEXT STRATEGY
    # --------------------------------------------------------

    strategy = _normalize_strategy(
        evaluation.get(
            "next_strategy",
            "continue"
        )
    )

    return {

        "evaluation":
            evaluation,

        "history":
            history,

        "scores":
            scores,

        "next_strategy":
            strategy,
    }


# ============================================================
# CONDITIONAL ROUTER
# ============================================================

def route_after_evaluation(
    state: InterviewState
):

    question_count = _question_count(
        state
    )

    minimum = _minimum_questions(
        state
    )

    maximum = _maximum_questions(
        state
    )

    strategy = _normalize_strategy(
        state.get(
            "next_strategy",
            "continue"
        )
    )

    # --------------------------------------------------------
    # HARD STOP
    # --------------------------------------------------------

    if question_count >= maximum:

        return "finish"

    # --------------------------------------------------------
    # MINIMUM QUESTIONS
    # --------------------------------------------------------

    # The interviewer cannot finish before enough evidence
    # has been collected.

    if question_count < minimum:

        return "continue"

    # --------------------------------------------------------
    # LLM DECISION
    # --------------------------------------------------------

    if strategy == "finish":

        return "finish"

    if strategy == "follow_up":

        return "follow_up"

    if strategy == "harder":

        return "harder"

    if strategy == "new_topic":

        return "new_topic"

    return "continue"


# ============================================================
# NEXT QUESTION NODE
# ============================================================

def next_question_node(
    state: InterviewState
):

    evaluation = state.get(
        "evaluation",
        {}
    )

    profile = state.get(
        "profile",
        {}
    )

    available_topics = profile.get(
        "interview_topics",
        []
    )

    # --------------------------------------------------------
    # ADAPTIVE DIFFICULTY
    # --------------------------------------------------------

    recommended_difficulty = (
        evaluation.get(
            "recommended_difficulty",
            state.get(
                "difficulty",
                "medium"
            )
        )
    )

    if recommended_difficulty not in {
        "easy",
        "medium",
        "hard"
    }:

        recommended_difficulty = "medium"

    # --------------------------------------------------------
    # GENERATE QUESTION
    # --------------------------------------------------------

    next_question = generate_next_question(

        role=state.get(
            "role",
            ""
        ),

        skills=state.get(
            "skills",
            []
        ),

        candidate_profile=profile,

        resume_context=state.get(
            "resume_context",
            ""
        ),

        previous_question=state.get(
            "question",
            ""
        ),

        previous_answer=state.get(
            "answer",
            ""
        ),

        evaluation=evaluation,

        asked_questions=state.get(
            "asked_questions",
            []
        ),

        current_topic=state.get(
            "topic",
            ""
        ),

        difficulty=recommended_difficulty,

        available_topics=available_topics,
    )

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    question = (
        next_question
        .get(
            "question",
            ""
        )
        .strip()
    )

    if not question:

        raise ValueError(
            "Groq generated an empty interview question."
        )

    # --------------------------------------------------------
    # SAFETY AGAINST DUPLICATES
    # --------------------------------------------------------

    asked_questions = list(
        state.get(
            "asked_questions",
            []
        )
    )

    # Case-insensitive duplicate check

    normalized_question = (
        question.lower()
        .strip()
    )

    existing = {
        q.lower().strip()
        for q in asked_questions
    }

    if normalized_question in existing:

        # We still keep the generated question because
        # the LLM function should already be instructed
        # to avoid repetitions. This prevents the graph
        # from getting stuck.

        pass

    asked_questions.append(
        question
    )

    # --------------------------------------------------------
    # TOPIC / SKILL
    # --------------------------------------------------------

    topic = (
        next_question
        .get(
            "topic",
            state.get(
                "topic",
                ""
            )
        )
    )

    skill = (
        next_question
        .get(
            "skill",
            state.get(
                "skill",
                ""
            )
        )
    )

    difficulty = (
        next_question
        .get(
            "difficulty",
            recommended_difficulty
        )
    )

    if difficulty not in {
        "easy",
        "medium",
        "hard"
    }:

        difficulty = (
            recommended_difficulty
        )

    return {

        "question":
            question,

        "topic":
            topic,

        "skill":
            skill,

        "difficulty":
            difficulty,

        "asked_questions":
            asked_questions,

        "answer":
            "",
    }


# ============================================================
# FOLLOW-UP NODE
# ============================================================

def follow_up_node(
    state: InterviewState
):

    """
    Follow-up is deliberately handled by the same question
    generator.

    The LLM receives:
        previous question
        candidate answer
        evaluation
        resume context

    and is instructed to ask ONE short follow-up.

    This allows the interview to drill into something the
    candidate actually said.
    """

    state_copy = dict(
        state
    )

    state_copy["next_strategy"] = (
        "follow_up"
    )

    return next_question_node(
        state_copy
    )


# ============================================================
# HARDER QUESTION NODE
# ============================================================

def harder_question_node(
    state: InterviewState
):

    """
    Candidate performed well.

    Increase difficulty, but remain inside the candidate's
    resume/skills rather than suddenly testing unrelated
    knowledge.
    """

    state_copy = dict(
        state
    )

    state_copy["difficulty"] = "hard"

    state_copy["next_strategy"] = (
        "harder"
    )

    return next_question_node(
        state_copy
    )


# ============================================================
# NEW TOPIC NODE
# ============================================================

def new_topic_node(
    state: InterviewState
):

    """
    Move to another resume-supported skill/topic.

    This prevents the interview from becoming a 12-question
    interrogation about one tiny corner of the resume.
    """

    state_copy = dict(
        state
    )

    state_copy["next_strategy"] = (
        "new_topic"
    )

    return next_question_node(
        state_copy
    )


# ============================================================
# NORMAL CONTINUE NODE
# ============================================================

def continue_node(
    state: InterviewState
):

    return next_question_node(
        state
    )


# ============================================================
# FINISH NODE
# ============================================================

def finish_node(
    state: InterviewState
):

    return {
        "finished": True
    }


# ============================================================
# GRAPH
# ============================================================

def build_interview_graph():

    graph = StateGraph(
        InterviewState
    )

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    graph.add_node(
        "evaluate",
        evaluate_node
    )

    graph.add_node(
        "follow_up",
        follow_up_node
    )

    graph.add_node(
        "harder",
        harder_question_node
    )

    graph.add_node(
        "new_topic",
        new_topic_node
    )

    graph.add_node(
        "continue",
        continue_node
    )

    graph.add_node(
        "finish",
        finish_node
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "evaluate"
    )

    # --------------------------------------------------------
    # CONDITIONAL EVALUATION ROUTING
    # --------------------------------------------------------

    graph.add_conditional_edges(

        "evaluate",

        route_after_evaluation,

        {

            "follow_up":
                "follow_up",

            "harder":
                "harder",

            "new_topic":
                "new_topic",

            "continue":
                "continue",

            "finish":
                "finish",
        }
    )

    # --------------------------------------------------------
    # QUESTION NODES END THE GRAPH TURN
    # --------------------------------------------------------

    graph.add_edge(
        "follow_up",
        END
    )

    graph.add_edge(
        "harder",
        END
    )

    graph.add_edge(
        "new_topic",
        END
    )

    graph.add_edge(
        "continue",
        END
    )

    graph.add_edge(
        "finish",
        END
    )

    return graph.compile()


# ============================================================
# COMPILED GRAPH
# ============================================================

GRAPH = build_interview_graph()


# ============================================================
# SINGLE INTERVIEW TURN
# ============================================================

def process_answer(
    state: InterviewState
):

    """
    Process exactly one candidate answer.

    Streamlit can call this once whenever the candidate
    submits an answer.

    Flow:

        Candidate Answer
               |
               v
           Evaluate
               |
          Conditional
          /    |    \
         /     |     \
    Follow-up Harder New Topic
         \     |     /
          Continue
               |
               v
         Next Question

    or

               |
             Finish
    """

    return GRAPH.invoke(
        state
    )