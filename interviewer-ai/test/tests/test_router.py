def route_question(question_type):
    routes = {
        "technical": "technical_interview",
        "behavioral": "behavioral_interview",
        "hr": "hr_interview"
    }

    return routes.get(question_type, "general_interview")


def test_technical_route():
    assert route_question("technical") == "technical_interview"


def test_behavioral_route():
    assert route_question("behavioral") == "behavioral_interview"


def test_hr_route():
    assert route_question("hr") == "hr_interview"


def test_unknown_route():
    assert route_question("unknown") == "general_interview"