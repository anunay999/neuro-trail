import logging
from typing import List, Dict, Any, Optional
import uuid
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.core.plugin_base import KnowledgeGraphPlugin
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class Neo4jDocumentGraph(KnowledgeGraphPlugin):
    """Plugin for Neo4j document knowledge graph"""
    
    plugin_type = "knowledge_graph"
    plugin_name = "neo4j"
    plugin_version = "0.1.0"
    plugin_description = "Neo4j document knowledge graph"
    
    def __init__(self):
        """Initialize Neo4j document graph plugin"""
        self.initialized = False
        self.driver = None
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize the plugin
        
        Args:
            **kwargs: Additional parameters
                - uri: Optional Neo4j URI override
                - user: Optional Neo4j username override
                - password: Optional Neo4j password override
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Get settings from kwargs or use defaults
            self.uri = kwargs.get("uri") or self.uri
            self.user = kwargs.get("user") or self.user
            self.password = kwargs.get("password") or self.password
            
            # Check if settings are valid
            if not self.uri or not self.user or not self.password:
                logger.error("Neo4j connection settings incomplete")
                return False
            
            # Initialize Neo4j driver
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=basic_auth(self.user, self.password)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS num")
                record = result.single()
                if record["num"] != 1:
                    logger.error("Neo4j connection test failed")
                    return False
            
            # Create indexes and constraints if not exist
            self._init_schema()
            
            self.initialized = True
            logger.info(f"Neo4j document graph initialized with URI: {self.uri}")
            return True
            
        except ServiceUnavailable:
            logger.error(f"Neo4j service unavailable at {self.uri}")
            return False
        except AuthError:
            logger.error(f"Neo4j authentication error with user: {self.user}")
            return False
        except Exception as e:
            logger.exception(f"Error initializing Neo4j document graph: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful
        """
        if self.driver:
            self.driver.close()
        
        self.driver = None
        self.initialized = False
        logger.info("Neo4j document graph shutdown")
        return True
    
    async def add_book(
        self,
        title: str,
        author: str,
        **kwargs
    ) -> bool:
        """
        Add a book to the knowledge graph
        
        Args:
            title: Book title
            author: Book author
            **kwargs: Additional parameters
                - metadata: Optional book metadata
                
        Returns:
            bool: True if successful
        """
        if not self.initialized:
            logger.error("Neo4j document graph not initialized")
            return False
        
        try:
            metadata = kwargs.get("metadata", {})
            
            with self.driver.session() as session:
                query = """
                MERGE (b:Book {title: $title})
                SET b.updated_at = datetime()
                FOREACH (k IN keys($metadata) | SET b[k] = $metadata[k])
                
                MERGE (a:Author {name: $author})
                MERGE (a)-[:WROTE]->(b)
                RETURN b
                """
                
                result = session.run(
                    query, 
                    title=title, 
                    author=author, 
                    metadata=metadata
                )
                
                # Check if result has a record
                return result.single() is not None
                
        except Exception as e:
            logger.exception(f"Error adding book to Neo4j: {e}")
            return False
    
    async def add_chapters(
        self,
        book_title: str,
        chapters: List[Dict[str, Any]],
        **kwargs
    ) -> bool:
        """
        Add chapters to a book in the knowledge graph
        
        Args:
            book_title: Book title
            chapters: List of chapter dictionaries with 'title' and 'seq' keys
            **kwargs: Additional parameters
                
        Returns:
            bool: True if successful
        """
        if not self.initialized:
            logger.error("Neo4j document graph not initialized")
            return False
        
        if not chapters:
            logger.warning(f"No chapters provided for book: {book_title}")
            return True  # Not an error, just nothing to do
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (b:Book {title: $title})
                UNWIND $chapters as chapter
                MERGE (c:Chapter {
                    title: chapter.title, 
                    seq: chapter.seq
                })
                MERGE (b)-[:HAS_CHAPTER]->(c)
                RETURN count(c) as chapter_count
                """
                
                result = session.run(
                    query, 
                    title=book_title, 
                    chapters=chapters
                )
                
                record = result.single()
                chapter_count = record["chapter_count"] if record else 0
                
                logger.info(f"Added {chapter_count} chapters to book '{book_title}'")
                return chapter_count > 0
                
        except Exception as e:
            logger.exception(f"Error adding chapters to Neo4j: {e}")
            return False
    
    def _init_schema(self):
        """Initialize Neo4j schema with indexes and constraints"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # Create constraints for primary nodes
                constraints = [
                    "CREATE CONSTRAINT book_title IF NOT EXISTS FOR (b:Book) REQUIRE b.title IS UNIQUE",
                    "CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
                    "CREATE CONSTRAINT chapter_unique IF NOT EXISTS FOR (c:Chapter) REQUIRE (c.title, c.seq) IS UNIQUE"
                ]
                
                # Create indexes for common searches
                indexes = [
                    "CREATE INDEX book_title_idx IF NOT EXISTS FOR (b:Book) ON (b.title)",
                    "CREATE INDEX author_name_idx IF NOT EXISTS FOR (a:Author) ON (a.name)",
                    "CREATE INDEX chapter_title_idx IF NOT EXISTS FOR (c:Chapter) ON (c.title)"
                ]
                
                # Execute schema operations
                for query in constraints + indexes:
                    try:
                        session.run(query)
                    except Exception as e:
                        logger.warning(f"Error creating schema: {e}")
                        # Continue with other schema operations
                
                logger.info("Neo4j schema initialized")
                
        except Exception as e:
            logger.exception(f"Error initializing Neo4j schema: {e}")