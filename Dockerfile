# Use Ollama as the base image (includes Ollama pre-installed)
FROM ollama/ollama:latest AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONIOENCODING=UTF-8 \
    DEBIAN_FRONTEND=noninteractive

# Application-specific environment variables
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=password
ENV OLLAMA_URL=http://localhost:11434/api/generate

# Add deadsnakes PPA to install Python 3.11 on Ubuntu 20.04 (Focal)
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    curl \
    git \
    unzip \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure Python 3.11 is the default
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && ln -sf /usr/bin/pip3 /usr/bin/pip

# Create a virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install uv package manager
RUN pip install --upgrade pip && pip install uv

# Set the working directory
WORKDIR /app

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install -r pyproject.toml

# Copy the rest of the application
COPY src/ src/
COPY .env /app/.env  

# Copy configuration files
COPY config/redis.conf /etc/redis/redis.conf
COPY config/neo4j.conf /etc/neo4j/neo4j.conf

# Install and configure Redis
RUN apt-get update && apt-get install -y redis-server
RUN mkdir -p /var/lib/redis && chown redis:redis /var/lib/redis

# Install and configure Neo4j
RUN mkdir -p /var/lib/neo4j
RUN wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - \
    && echo 'deb https://debian.neo4j.com stable main' | tee /etc/apt/sources.list.d/neo4j.list \
    && apt-get update && apt-get install -y neo4j \
    && rm -rf /var/lib/apt/lists/*

# Expose ports for services
EXPOSE 7687 7474 6379 11434

# Set entry point to run everything at runtime
CMD export $(grep -v '^#' /app/.env | xargs) && \
    service neo4j start && \
    redis-server /etc/redis/redis.conf & \
    sleep 5 && \
    python src/main.py --book-path=/workspaces/neuro-trail/books