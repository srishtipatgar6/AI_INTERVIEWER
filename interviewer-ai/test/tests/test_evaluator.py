def evaluate_answer(answer):
    """
    Simple answer evaluator.
    Returns a score from 0 to 10.
    """

    if not answer or not answer.strip():
        return 0

    word_count = len(answer.split())

    if word_count < 5:
        return 3
    elif word_count < 15:
        return 6
    elif word_count < 30:
        return 8
    else:
        return 10


def test_empty_answer():
    assert evaluate_answer("") == 0


def test_short_answer():
    assert evaluate_answer("I know Python") == 3


def test_medium_answer():
    answer = "I have experience developing applications using Python and Django."
    assert evaluate_answer(answer) == 6


def test_good_answer():
    answer = (
        "I have several years of experience developing Python applications. "
        "I have worked with APIs, databases, testing, and deployment."
    )

    assert evaluate_answer(answer) == 8