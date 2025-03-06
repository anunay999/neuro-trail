import streamlit as st
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ClientError, ServiceUnavailable

from core.settings import settings

# -------------------------------------------
# Build Knowledge graph on Neo4j
# -------------------------------------------


class KnowledgeGraph:
    def __init__(self):
        self.driver = None  # Initialize driver to None
        self.connect()

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
            with self.driver.session() as session:  # Verify connectivity immediately
                session.run("RETURN 1")
            # Show success in Streamlit
            print("Successfully connected to Neo4j database.")
        except ServiceUnavailable:
            st.toast(
                "Database connection error: Neo4j server is unavailable.  Please ensure the Neo4j server is running and accessible.",
                icon="⚠️",
            )
        except AuthError:
            st.toast(
                f"Authentication error:  Invalid Neo4j credentials. Please check NEO4J_USER-> {settings.neo4j_user} and NEO4J_PASSWORD-> {settings.neo4j_password}.",
                icon="⚠️",
            )
        except ClientError as e:
            # More specific client-side errors
            st.toast(f"Client error: {e}", icon="⚠️")
        except Exception as e:
            st.toast(f"An unexpected error occurred: {e}", icon="⚠️")

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                st.error(f"Error closing the database connection: {e}")

    def _run_query(self, query, **params):
        """Helper function to run queries and handle exceptions."""
        if not self.driver:
            st.error("Database connection is not established.")
            return  # Or raise an exception, depending on desired behavior

        try:
            with self.driver.session() as session:
                return session.run(query, params)
        except ServiceUnavailable:
            st.error(
                "Database connection error: Neo4j server became unavailable during the operation."
            )
        except ClientError as e:
            st.error(f"Query error: {e}")  # Show query errors in Streamlit
        except Exception as e:
            st.error(f"An unexpected error occurred during query execution: {e}")

    def add_book(self, title, author):
        query = """
        MERGE (b:Book {title: $title})
        MERGE (a:Author {name: $author})
        MERGE (a)-[:WROTE]->(b)
        RETURN b
        """
        self._run_query(query, title=title, author=author)

    def add_chapters(self, book_title, chapters):
        """
        Inserts chapter nodes and links them to the book.
        Each chapter dict should have keys 'title' and 'seq'.
        """
        query = """
        MATCH (b:Book {title: $title})
        UNWIND $chapters as chapter
        MERGE (c:Chapter {title: chapter.title, seq: chapter.seq})
        MERGE (b)-[:HAS_CHAPTER]->(c)
        """
        self._run_query(query, title=book_title, chapters=chapters)
