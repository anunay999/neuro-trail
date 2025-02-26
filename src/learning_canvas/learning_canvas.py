from knowledge_graph import KnowledgeGraph
from vector_store import VectorStore
from user_memory import UserMemory
from epub_extract import extract_epub
from llm import query_ollama
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class LearningCanvas:
    def __init__(self):
        # Initialize components (adjust connection details as needed)
        self.kg = KnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        self.vector_store = VectorStore()
        self.memory = UserMemory()

    def add_epub(self, epub_path, user_id="user_123"):
        # Process EPUB file
        metadata, full_text, chapters = extract_epub(epub_path)
        print(f"Loaded '{metadata['title']}' by {metadata['author']}. Chapters found: {len(chapters)}")

        # Update Knowledge Graph
        self.kg.add_book(metadata['title'], metadata['author'])
        if chapters:
            self.kg.add_chapters(metadata['title'], chapters)
        self.kg.add_user_interaction(user_id, metadata['title'])

        # Update Vector Store with text chunks (using paragraph splitting)
        paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 50]
        self.vector_store.add_text_chunks(paragraphs)

        # Update User Memory with progress
        self.memory.update_progress(user_id, metadata['title'])
        print("EPUB processed and added to system.")

    def search_query(self, query):
        results = self.vector_store.search(query)
        for res in results:
            chapter_info = f"(Chapter: {res['chapter']})" if res.get("chapter") else ""
            print(f"Result {chapter_info}:\n{res['text'][:200]}...\n")

    def answer_query(self, query, user_id="user_123"):
        """
        Uses the vector store to fetch context and then sends a prompt (context + query)
        to the Ollama LLM model. Then, it asks the user if they understood the response and
        collects a summary to update their learning memory.
        """
        # Fetch context chunks
        context_chunks = self.vector_store.search(query, top_k=5)
        context_text = "\n".join([chunk["text"] for chunk in context_chunks])
        prompt = f"Using the following context:\n{context_text}\n\nAnswer the following question:\n{query}"
        answer = query_ollama(prompt)
        print("\nAnswer from Ollama LLM:")
        print(answer)

        # Ask the user to confirm if they understood
        understood = input("\nDid you understand the answer? (y/n): ").strip().lower()
        if understood == 'y':
            # TODO: quiz
            # summary = input("Great! Please provide a brief summary of what you learned: ")
            self.memory.update_learning_summary(user_id, answer)
            print("Learning summary updated.")
        else:
            feedback = input("Can you provide feedback to improve the response: ")
            user_prompt  = f"goal:improve the response based on user feedback\n Current Answer: {answer}\n\nuser feedback on improvement:\n{feedback}\n incorporate the feedback and improve the current response"
            self.answer_query(user_prompt)
        return answer

    def get_user_history(self, user_id="user_123"):
        progress = self.memory.get_history(user_id)
        learned = self.memory.get_learning_history(user_id)
        print("Books read:", progress)
        print("Learning summaries:")
        for idx, summary in enumerate(learned, 1):
            print(f"{idx}. {summary}")

    def close(self):
        self.kg.close()