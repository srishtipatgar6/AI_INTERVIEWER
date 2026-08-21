from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from .embeddings import get_embeddings


class BaseVectorStore:

    def __init__(self):

        self.embeddings = get_embeddings()
        self.store = None

    def _chunk_text(
        self,
        text,
        chunk_size=900,
        overlap=150,
    ):

        text = text.replace(
            "\r",
            "",
        )

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n")
            if paragraph.strip()
        ]

        chunks = []
        current = ""

        for paragraph in paragraphs:

            if len(current) + len(paragraph) <= chunk_size:

                current += paragraph + "\n"

            else:

                if current.strip():
                    chunks.append(
                        current.strip()
                    )

                overlap_text = (
                    current[-overlap:]
                    if current
                    else ""
                )

                current = (
                    overlap_text
                    + "\n"
                    + paragraph
                    + "\n"
                )

        if current.strip():

            chunks.append(
                current.strip()
            )

        return chunks

    def retrieve(
        self,
        query,
        k=4,
    ):

        if self.store is None:
            return []

        results = (
            self.store.similarity_search_with_score(
                query,
                k=k,
            )
        )

        output = []

        for document, distance in results:

            output.append(
                {
                    "text": document.page_content,
                    "score": float(distance),
                    "metadata": document.metadata,
                }
            )

        return output


class ResumeVectorStore(BaseVectorStore):

    def build_resume_index(
        self,
        resume_text,
    ):

        chunks = self._chunk_text(
            resume_text
        )

        documents = []

        for index, chunk in enumerate(chunks):

            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": "resume",
                        "chunk_id": index,
                    },
                )
            )

        self.store = FAISS.from_documents(
            documents,
            self.embeddings,
        )


class KnowledgeVectorStore(BaseVectorStore):

    def build(
        self,
        knowledge_text,
    ):

        chunks = self._chunk_text(
            knowledge_text,
            chunk_size=1000,
            overlap=150,
        )

        documents = []

        for index, chunk in enumerate(chunks):

            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": "interview_knowledge",
                        "chunk_id": index,
                    },
                )
            )

        self.store = FAISS.from_documents(
            documents,
            self.embeddings,
        )