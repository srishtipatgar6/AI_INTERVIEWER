from concurrent.futures import ThreadPoolExecutor

from .llm import (
    resume_llm,
    question_llm,
    evaluation_llm,
    semantic_llm,
    final_llm,
)

from .prompts import (
    RESUME_PROMPT,
    QUESTION_PROMPT,
    EVALUATION_PROMPT,
    SEMANTIC_PROMPT,
    FINAL_PROMPT,
)


def analyze_resume(
    resume_text,
    role,
    skills,
):

    prompt = RESUME_PROMPT.format(
        role=role,
        skills=", ".join(skills),
        resume=resume_text,
    )

    return resume_llm.invoke(
        prompt
    ).model_dump()


def generate_question_candidates(
    state,
    resume_retriever,
    knowledge_retriever,
):

    current_question = state.get(
        "current_question",
        {},
    )

    answer = state.get(
        "current_answer",
        "",
    )

    query = f"""
Role: {state["target_role"]}

Skills:
{", ".join(state["target_skills"])}

Current question:
{current_question}

Candidate answer:
{answer}

Weak areas:
{state.get("weak_areas", [])}

Strong areas:
{state.get("strong_areas", [])}

Find evidence relevant to deciding
the next interview question.
"""

    # --------------------------------------------------------
    # PARALLEL RAG RETRIEVAL
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        resume_future = executor.submit(
            resume_retriever,
            query,
        )

        knowledge_future = executor.submit(
            knowledge_retriever,
            query,
        )

        resume_context = resume_future.result()
        knowledge_context = knowledge_future.result()

    resume_text = "\n\n".join(
        item["text"]
        for item in resume_context
    )

    knowledge_text = "\n\n".join(
        item["text"]
        for item in knowledge_context
    )

    prompt = QUESTION_PROMPT.format(

        name=state["name"],

        role=state["target_role"],

        skills=", ".join(
            state["target_skills"]
        ),

        resume_profile=state.get(
            "resume_profile",
            {},
        ),

        resume_context=resume_text,

        knowledge_context=knowledge_text,

        transcript=state.get(
            "transcript",
            [],
        )[-8:],

        skill_scores=state.get(
            "skill_scores",
            {},
        ),

        confidence=state.get(
            "skill_confidence",
            {},
        ),

        current_question=current_question,

        answer=answer,

        evaluation=state.get(
            "current_evaluation",
            {},
        ),
    )

    candidates = question_llm.invoke(
        prompt
    ).model_dump()

    return {
        "candidates": candidates,
        "resume_context": resume_context,
        "knowledge_context": knowledge_context,
    }


def evaluate_answer_parallel(
    state,
    resume_retriever,
    knowledge_retriever,
):

    question = state[
        "current_question"
    ]

    answer = state[
        "current_answer"
    ]

    query = f"""
Question:
{question["question"]}

Skill:
{question["skill"]}

Candidate answer:
{answer}
"""

    # --------------------------------------------------------
    # PARALLEL RETRIEVAL
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        resume_future = executor.submit(
            resume_retriever,
            query,
        )

        knowledge_future = executor.submit(
            knowledge_retriever,
            query,
        )

        resume_context = resume_future.result()
        knowledge_context = knowledge_future.result()

    resume_text = "\n\n".join(
        item["text"]
        for item in resume_context
    )

    knowledge_text = "\n\n".join(
        item["text"]
        for item in knowledge_context
    )

    evaluation_prompt = EVALUATION_PROMPT.format(
        role=state["target_role"],
        skill=question["skill"],
        question=question["question"],
        answer=answer,
        resume_context=resume_text,
        knowledge_context=knowledge_text,
    )

    semantic_prompt = SEMANTIC_PROMPT.format(
        question=question["question"],
        answer=answer,
    )

    # --------------------------------------------------------
    # PARALLEL LLM EVALUATION
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        evaluation_future = executor.submit(
            evaluation_llm.invoke,
            evaluation_prompt,
        )

        semantic_future = executor.submit(
            semantic_llm.invoke,
            semantic_prompt,
        )

        evaluation = (
            evaluation_future
            .result()
            .model_dump()
        )

        semantic = (
            semantic_future
            .result()
            .model_dump()
        )

    return {
        "evaluation": evaluation,
        "semantic": semantic,
        "resume_context": resume_context,
        "knowledge_context": knowledge_context,
    }


def update_knowledge(
    state,
):

    evaluation = state[
        "current_evaluation"
    ]

    skill = state[
        "current_question"
    ]["skill"]

    score = float(
        evaluation["score"]
    )

    confidence_value = float(
        evaluation.get(
            "confidence",
            score / 10,
        )
    )

    scores = dict(
        state.get(
            "skill_scores",
            {},
        )
    )

    confidence = dict(
        state.get(
            "skill_confidence",
            {},
        )
    )

    previous_score = scores.get(
        skill,
        0,
    )

    previous_confidence = confidence.get(
        skill,
        0,
    )

    if previous_confidence == 0:

        new_score = score

    else:

        new_score = (
            previous_score * 0.60
            + score * 0.40
        )

    new_confidence = min(
        0.95,
        previous_confidence
        + (
            0.20
            * confidence_value
        ),
    )

    scores[skill] = round(
        new_score,
        2,
    )

    confidence[skill] = round(
        new_confidence,
        2,
    )

    covered = list(
        state.get(
            "covered_skills",
            [],
        )
    )

    if skill not in covered:
        covered.append(skill)

    weak = list(
        state.get(
            "weak_areas",
            [],
        )
    )

    strong = list(
        state.get(
            "strong_areas",
            [],
        )
    )

    if score <= 4 and skill not in weak:
        weak.append(skill)

    if score >= 8 and skill not in strong:
        strong.append(skill)

    claims_tested = list(
        state.get(
            "resume_claims_tested",
            [],
        )
    )

    claims_verified = list(
        state.get(
            "resume_claims_verified",
            [],
        )
    )

    resume_evidence = state[
        "current_question"
    ].get(
        "resume_evidence",
        "",
    )

    if resume_evidence:

        if skill not in claims_tested:

            claims_tested.append(
                skill
            )

        if score >= 7:

            if skill not in claims_verified:

                claims_verified.append(
                    skill
                )

    return {
        "skill_scores": scores,
        "skill_confidence": confidence,
        "covered_skills": covered,
        "weak_areas": weak,
        "strong_areas": strong,
        "resume_claims_tested": claims_tested,
        "resume_claims_verified": claims_verified,
    }


def select_question(
    state,
    candidates,
):

    evaluation = state.get(
        "current_evaluation",
        {},
    )

    score = evaluation.get(
        "score",
        5,
    )

    current_skill = state.get(
        "current_question",
        {},
    ).get(
        "skill",
        "",
    )

    confidence = state.get(
        "skill_confidence",
        {},
    )

    target_skills = state.get(
        "target_skills",
        [],
    )

    covered = state.get(
        "covered_skills",
        [],
    )

    uncovered = [
        skill
        for skill in target_skills
        if skill not in covered
    ]

    # Weak answer -> follow-up
    if score <= 4:

        return (
            candidates["follow_up"],
            "follow_up",
        )

    # Strong answer -> deep dive
    if score >= 8:

        if confidence.get(
            current_skill,
            0,
        ) < 0.85:

            return (
                candidates["deep_dive"],
                "deep_dive",
            )

    # New skill -> explore
    if uncovered:

        return (
            candidates["skill_exploration"],
            "skill_exploration",
        )

    # Otherwise continue deepening
    return (
        candidates["deep_dive"],
        "deep_dive",
    )


def generate_final_evaluation(
    state,
):

    prompt = FINAL_PROMPT.format(

        candidate=state["name"],

        role=state["target_role"],

        skills=state[
            "target_skills"
        ],

        resume_profile=state.get(
            "resume_profile",
            {},
        ),

        transcript=state.get(
            "transcript",
            [],
        ),

        skill_scores=state.get(
            "skill_scores",
            {},
        ),

        confidence=state.get(
            "skill_confidence",
            {},
        ),

        claims_tested=state.get(
            "resume_claims_tested",
            [],
        ),

        claims_verified=state.get(
            "resume_claims_verified",
            [],
        ),
    )

    return final_llm.invoke(
        prompt
    ).model_dump()