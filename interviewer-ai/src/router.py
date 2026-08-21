def choose_question_strategy(state):

    evaluations = state.get(
        "evaluations",
        []
    )

    # First question
    if not evaluations:

        return {
            "strategy": "fundamental",
            "skill": choose_uncovered_skill(state),
            "difficulty": "medium",
        }

    latest = evaluations[-1]

    score = latest["score"]
    skill = latest["skill"]

    confidence = state[
        "skill_confidence"
    ].get(
        skill,
        0
    )

    # --------------------------------
    # Weak answer
    # --------------------------------

    if score <= 4:

        return {
            "strategy": "follow_up",
            "skill": skill,
            "difficulty": "easy",
        }

    # --------------------------------
    # Strong answer
    # --------------------------------

    if (
        score >= 8
        and confidence >= 0.5
    ):

        return {
            "strategy": "deep_dive",
            "skill": skill,
            "difficulty": "hard",
        }

    # --------------------------------
    # Explore another skill
    # --------------------------------

    return {
        "strategy": "skill_exploration",
        "skill": choose_uncovered_skill(
            state
        ),
        "difficulty": "medium",
    }


def choose_uncovered_skill(state):

    skills = state[
        "target_skills"
    ]

    covered = state[
        "covered_skills"
    ]

    # First preference:
    # completely unexplored skill

    for skill in skills:

        if skill not in covered:

            return skill

    # --------------------------------
    # Everything explored
    # Choose lowest-confidence skill
    # --------------------------------

    confidence = state[
        "skill_confidence"
    ]

    return min(
        skills,
        key=lambda skill:
            confidence.get(skill, 0)
    )