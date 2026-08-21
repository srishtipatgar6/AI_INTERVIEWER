from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# EMBEDDINGS
# ============================================================

_embeddings = None


def get_embeddings():

    global _embeddings

    if _embeddings is None:

        _embeddings = HuggingFaceEmbeddings(
            model_name=(
                "sentence-transformers/"
                "all-MiniLM-L6-v2"
            ),
            model_kwargs={
                "device": "cpu"
            },
            encode_kwargs={
                "normalize_embeddings": True
            },
        )

    return _embeddings


# ============================================================
# BUILD RESUME VECTORSTORE
# ============================================================

def build_resume_vectorstore(
    resume_text: str
):

    if not resume_text or not resume_text.strip():

        raise ValueError(
            "Resume text is empty."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
        ],
    )

    chunks = splitter.split_text(
        resume_text
    )

    documents: List[Document] = []

    for index, chunk in enumerate(chunks):

        if not chunk.strip():
            continue

        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": "candidate_resume",
                    "chunk": index,
                },
            )
        )

    if not documents:

        raise ValueError(
            "Could not create resume chunks."
        )

    vectorstore = FAISS.from_documents(
        documents,
        get_embeddings()
    )

    return vectorstore


# ============================================================
# RETRIEVE RESUME CONTEXT
# ============================================================

def retrieve_resume_context(
    vectorstore,
    query: str,
    k: int = 4,
) -> str:

    if vectorstore is None:

        raise ValueError(
            "Resume vectorstore is not initialized."
        )

    documents = vectorstore.similarity_search(
        query,
        k=k
    )

    if not documents:

        return ""

    return "\n\n---\n\n".join(
        document.page_content
        for document in documents
    )