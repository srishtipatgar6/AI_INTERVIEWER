from pathlib import Path
from pypdf import PdfReader
from docx import Document


def extract_resume_text(uploaded_file) -> str:

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    if filename.endswith(".docx"):
        document = Document(uploaded_file)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    if filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")

    raise ValueError(
        "Unsupported resume format. "
        "Please upload PDF, DOCX, or TXT."
    )