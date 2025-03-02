import os
import tempfile

from dotenv import load_dotenv

# Import the updated embedding model enum
from enums import EmbeddingModel, Model, Provider
from epub_extract import extract_epub
from knowledge_graph import KnowledgeGraph
from llm import get_llm
from rag import VectorStore

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class LearningCanvas:
    def __init__(self):
        # Initialize components (adjust connection details as needed)
        self.kg = KnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        self.model = None
        self.embedding_model = None
        self.vector_store = None  # Initialized later after model is set

    def set_model(self, model: Model, embedding_model: EmbeddingModel):
        """
        Sets the LLM model and embedding model dynamically.
        """
        self.model = model
        self.embedding_model = embedding_model

        # Initialize the Vector Store with the selected embedding model
        self.vector_store = VectorStore(
            embedding_model=self.embedding_model,
            chapter_mode=True
        )

    def add_epub(self, epub_file, user_id="user_123"):
        """
        Process an uploaded EPUB file (file-like object) and add it to the system.
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
            # Write the uploaded file content
            temp_file.write(epub_file.read())
            temp_file_path = temp_file.name  # Save path for processing

        try:
            # Process EPUB file using the extracted path
            metadata, full_text, chapters = extract_epub(temp_file_path)
            print(
                f"Loaded '{metadata['title']}' by {metadata['author']}. Chapters found: {len(chapters)}"
            )

            # Update Knowledge Graph
            self.kg.add_book(metadata["title"], metadata["author"])
            if chapters:
                self.kg.add_chapters(metadata["title"], chapters)
            self.kg.add_user_interaction(user_id, metadata["title"])

            # Process text chunks & store in Vector Store
            paragraphs = [p.strip() for p in full_text.split(
                "\n\n") if len(p.strip()) > 50]
            self.vector_store.add_text_chunks(
                paragraphs, chapter=metadata["title"])

            # Update User Memory with progress
            # TODO: Implement user memory update
            print("EPUB processed and added to system.")

        finally:
            # Cleanup temporary file
            os.remove(temp_file_path)

    def search_query(self, query, top_k=3):
        """
        Searches for relevant text chunks using the vector store.
        """
        results = self.vector_store.search(query, top_k=top_k)
        for res in results:
            chapter_info = f"(Chapter: {res['chapter']})" if res.get(
                "chapter") else ""
            print(f"Result {chapter_info}:\n{res['text'][:200]}...\n")
        return results

    def answer_query(self, query, user_id="user_123"):
        """
        Uses the vector store to fetch context and then sends a prompt (context + query)
        to the LLM model.
        """
        print(f"Searching for relevant context for query: {query}")
        context_chunks = self.search_query(query, top_k=5)

        if not context_chunks:
            print("No relevant context found. Proceeding with default prompt.")
            prompt = f"Answer the following question:\n{query}"
        else:
            context_text = "\n".join([chunk["text"]
                                     for chunk in context_chunks])
            prompt = f"Using the following context:\n{context_text}\n\nAnswer the following question:\n{query}"

        llm = get_llm(self.model)
        response = llm(
            messages=[{"role": "user", "content": prompt}], temperature=0.7)
        return response

    def get_user_history(self, user_id="user_123"):
        """
        Retrieves the user's learning history.
        """
        # TODO : Add knowledge graph for user memory
        pass

    def close(self):
        """Closes connections to any resources."""
        self.kg.close()
