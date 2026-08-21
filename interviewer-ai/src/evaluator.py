from concurrent.futures import ThreadPoolExecutor

from .llm import (
    evaluation_llm,
    semantic_llm,
)

from .prompts import (
    EVALUATION_PROMPT,
    SEMANTIC_PROMPT,
)


def evaluate_answer_parallel(state):

    question = state["current_question"]
    answer = state["current_answer"]

    role = state["target_role"]
    skill = question["skill"]

    evaluation_prompt = EVALUATION_PROMPT.format(
        role=role,
        skill=skill,
        question=question["question"],
        answer=answer,
    )

    semantic_prompt = SEMANTIC_PROMPT.format(
        question=question["question"],
        answer=answer,
    )

    # ---------------------------------
    # PARALLEL EXECUTION
    # ---------------------------------

    with ThreadPoolExecutor(max_workers=2) as executor:

        evaluation_future = executor.submit(
            evaluation_llm.invoke,
            evaluation_prompt,
        )

        semantic_future = executor.submit(
            semantic_llm.invoke,
            semantic_prompt,
        )

        evaluation = evaluation_future.result()
        semantic = semantic_future.result()

    return {
        "evaluation": evaluation.model_dump(),
        "semantic": semantic.model_dump(),
    }