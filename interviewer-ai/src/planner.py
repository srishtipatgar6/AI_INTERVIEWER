from .llm import question_llm
from .prompts import QUESTION_PROMPT


def choose_strategy(state):

    evaluations = state.get("evaluations", [])

    if not evaluations:
        return "fundamental"

    latest = evaluations[-1]

    score = latest["score"]
    skill = latest["skill"]

    confidence = state["skill_confidence"].get(skill, 0)

    # Weak answer → follow up
    if score < 5:
        return "follow_up"

    # Strong answer with high confidence → move deeper
    if score >= 8 and confidence >= 0.65:
        return "deep_dive"

    # Otherwise explore uncovered skills
    return "skill_exploration"


def choose_target_skill(state, strategy):

    skills = state["target_skills"]

    covered = state.get("covered_skills", [])

    confidence = state.get("skill_confidence", {})

    if strategy in ("follow_up", "deep_dive"):

        evaluations = state.get("evaluations", [])

        if evaluations:
            return evaluations[-1]["skill"]

    # Pick least explored skill
    candidates = [
        skill for skill in skills
        if skill not in covered
    ]

    if candidates:
        return candidates[0]

    # If everything has been touched,
    # choose lowest-confidence skill.
    return min(
        skills,
        key=lambda s: confidence.get(s, 0)
    )


def generate_question(state):

    strategy = choose_strategy(state)

    target_skill = choose_target_skill(
        state,
        strategy
    )

    evaluations = state.get("evaluations", [])

    if evaluations:

        last_score = evaluations[-1]["score"]

        if last_score < 4:
            difficulty = "easy"

        elif last_score < 8:
            difficulty = "medium"

        else:
            difficulty = "hard"

    else:
        difficulty = "medium"

    prompt = QUESTION_PROMPT.format(
        name=state["name"],
        role=state["target_role"],
        skills=", ".join(state["target_skills"]),
        resume_profile=state["resume_profile"],
        transcript=state["transcript"][-5:],
        knowledge=state["skill_scores"],
        strategy=strategy,
        target_skill=target_skill,
        difficulty=difficulty,
    )

    question = question_llm.invoke(prompt)

    return question