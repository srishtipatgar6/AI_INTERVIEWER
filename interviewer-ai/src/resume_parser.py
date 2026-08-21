from io import BytesIO

from pypdf import PdfReader
from docx import Document


def extract_resume_text(uploaded_file):

    filename = uploaded_file.name.lower()

    data = uploaded_file.getvalue()

    # ========================================================
    # PDF
    # ========================================================

    if filename.endswith(".pdf"):

        reader = PdfReader(
            BytesIO(data)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text() or ""

            if text.strip():

                pages.append(
                    text.strip()
                )

        result = "\n".join(
            pages
        )

    # ========================================================
    # DOCX
    # ========================================================

    elif filename.endswith(".docx"):

        document = Document(
            BytesIO(data)
        )

        paragraphs = []

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:

                paragraphs.append(
                    text
                )

        result = "\n".join(
            paragraphs
        )

    # ========================================================
    # TXT
    # ========================================================

    elif filename.endswith(".txt"):

        result = data.decode(
            "utf-8",
            errors="ignore"
        )

    else:

        raise ValueError(
            "Unsupported resume format. "
            "Use PDF, DOCX or TXT."
        )

    if not result.strip():

        raise ValueError(
            "No readable text was found "
            "in the uploaded resume."
        )

    return result