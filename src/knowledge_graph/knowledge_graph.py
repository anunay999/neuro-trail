from neo4j import GraphDatabase

# -------------------------------------------
# Build Knowledge graph on Neo4j
# -------------------------------------------
class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_book(self, title, author):
        query = """
        MERGE (b:Book {title: $title})
        MERGE (a:Author {name: $author})
        MERGE (a)-[:WROTE]->(b)
        RETURN b
        """
        with self.driver.session() as session:
            session.run(query, title=title, author=author)

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
        with self.driver.session() as session:
            session.run(query, title=book_title, chapters=chapters)

    def add_user_interaction(self, user_id, book_title, interaction_type="READ"):
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (b:Book {title: $book_title})
        MERGE (u)-[r:INTERACTED {type: $interaction_type}]->(b)
        RETURN u, b
        """
        with self.driver.session() as session:
            session.run(query, user_id=user_id, book_title=book_title, interaction_type=interaction_type)