def parse_resume(resume_text):
    """
    Basic resume parser.
    Extracts simple information from resume text.
    """

    resume = {
        "name": None,
        "skills": []
    }

    lines = resume_text.splitlines()

    for line in lines:
        line = line.strip()

        if line.startswith("Name:"):
            resume["name"] = line.replace("Name:", "").strip()

        elif line.startswith("Skills:"):
            skills = line.replace("Skills:", "").strip()
            resume["skills"] = [
                skill.strip()
                for skill in skills.split(",")
                if skill.strip()
            ]

    return resume


def test_resume_name():
    resume = """
    Name: John Doe
    Skills: Python, SQL, Machine Learning
    """

    result = parse_resume(resume)

    assert result["name"] == "John Doe"


def test_resume_skills():
    resume = """
    Name: John Doe
    Skills: Python, SQL, Machine Learning
    """

    result = parse_resume(resume)

    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]
    assert "Machine Learning" in result["skills"]