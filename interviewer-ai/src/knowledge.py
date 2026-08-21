def update_knowledge(state):

    evaluation = state["current_evaluation"]

    skill = evaluation["skill"]
    score = evaluation["score"]

    scores = dict(
        state["skill_scores"]
    )

    confidence = dict(
        state["skill_confidence"]
    )

    previous_score = scores.get(
        skill,
        0.0
    )

    previous_confidence = confidence.get(
        skill,
        0.0
    )

    # ---------------------------------
    # Score update
    # ---------------------------------

    if previous_confidence == 0:

        new_score = float(score)

    else:

        new_score = (
            previous_score * 0.6
            + score * 0.4
        )

    # ---------------------------------
    # Confidence update
    # ---------------------------------

    new_confidence = min(
        0.95,
        previous_confidence + 0.20
    )

    scores[skill] = round(
        new_score,
        2
    )

    confidence[skill] = round(
        new_confidence,
        2
    )

    # ---------------------------------
    # Skill coverage
    # ---------------------------------

    covered = list(
        state["covered_skills"]
    )

    if skill not in covered:

        covered.append(skill)

    # ---------------------------------
    # Weak / strong areas
    # ---------------------------------

    weak = list(
        state["weak_areas"]
    )

    strong = list(
        state["strong_areas"]
    )

    if score < 5:

        if skill not in weak:
            weak.append(skill)

    if score >= 8:

        if skill not in strong:
            strong.append(skill)

    return {
        "skill_scores": scores,
        "skill_confidence": confidence,
        "covered_skills": covered,
        "weak_areas": weak,
        "strong_areas": strong,
    }