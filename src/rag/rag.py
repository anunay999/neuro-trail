import os

from langchain_community.graphs import Neo4jGraph

graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USER"],
    password=os.environ["NEO4J_PASSWORD"],
)
