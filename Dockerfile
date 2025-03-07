# Use the official Python image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install `uv` package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using `uv`
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync --locked

EXPOSE 8503

# Copy the entire application code into the container
COPY . .

# Set working directory to `src`
WORKDIR /app/src

# Start both Neo4j and the Python application
CMD ["/bin/bash", "-c", "\
    uv run streamlit run Configuration.py --server.port=8503"]
