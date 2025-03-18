import pickle
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from smolagents import Tool

from v2.rag.embedding_service import EmbeddingService
from v2.core.settings_config import settings

source_docs = [
    Document(page_content="Hello there", metadata={"source": f"page{str(i)}"})
    for i in range(100)
]

# docs_processed = text_splitter.split_documents(source_docs)


class RetrieverTool(Tool):
    name = "retriever"
    description = "Uses semantic search to retrieve the parts of transformers documentation that could be most relevant to answer your query."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be semantically close to your target documents. Use the affirmative form rather than a question.",
        }
    }
    output_type = "string"

    chroma_db_path = settings.persistant_storage_base / "chroma_db"
    dataset_path = settings.persistant_storage_base / "dataset.pkl"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_or_reload_dataset()

    def load_or_reload_dataset(self):
        # self.retriever = BM25Retriever.from_documents([], k=10)
        if self.dataset_path.exists():
            with open(self.dataset_path, "rb") as f:
                self.docs = pickle.load(f)
        else:
            self.docs = []

        self.embeddings = EmbeddingService()
        self.vector_store = Chroma(
            persist_directory=str(settings.persistant_storage_base / "chroma_db"),
            embedding_function=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            add_start_index=True,
            strip_whitespace=True,
            separators=["\n\n", "\n", ".", " ", ""],
        )

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        docs = self.vector_store.similarity_search(query, k=3)
        return "\nRetrieved documents:\n" + "".join(
            [
                f"\n\n===== Document {str(i)} =====\n" + doc.page_content
                for i, doc in enumerate(docs)
            ]
        )

    def add_docs(self, docs: list[Document]) -> None:
        self.vector_store.add_documents(docs)
        self.docs.extend(docs)
        with open(self.dataset_path, "wb") as f:
            pickle.dump(self.docs, f)

    def add_docs_from_str(
        self, docs: list[str], metadata: dict[str, str] | None = None
    ) -> None:
        docs = self.text_splitter.split_documents(
            [Document(page_content=doc, metadata=metadata) for doc in docs]
        )
        self.add_docs(docs)
