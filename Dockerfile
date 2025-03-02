# Use the official Python image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y curl default-jdk bash && rm -rf /var/lib/apt/lists/*

# Install Neo4j
ENV NEO4J_VERSION=5.11.0
RUN curl -fsSL https://neo4j.com/artifact.php?name=neo4j-community-${NEO4J_VERSION}-unix.tar.gz | tar -xz -C /usr/local \
    && mv /usr/local/neo4j-community-${NEO4J_VERSION} /usr/local/neo4j

# Set Neo4j environment variables
ENV NEO4J_HOME="/usr/local/neo4j"
ENV PATH="${NEO4J_HOME}/bin:${PATH}"
ENV NEO4J_AUTH="neo4j/password"

# Expose Neo4j ports
EXPOSE 7474 7687

EXPOSE 8501

# Install `uv` package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using `uv`
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync --locked

# Copy the entire application code into the container
COPY . .


# Set working directory to `src`
WORKDIR /app/src

# Start both Neo4j and the Python application
CMD ["/bin/bash", "-c", "\
    ${NEO4J_HOME}/bin/neo4j start && \
    sleep 10 && \
    uv run streamlit run app.py"]
