def test_initial_state():
    state = {
        "candidate_name": "John",
        "current_question": 1,
        "score": 0
    }

    assert state["candidate_name"] == "John"
    assert state["current_question"] == 1
    assert state["score"] == 0


def test_state_update():
    state = {
        "current_question": 1,
        "score": 0
    }

    state["current_question"] += 1
    state["score"] += 10

    assert state["current_question"] == 2
    assert state["score"] == 10