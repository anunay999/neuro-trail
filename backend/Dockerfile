# Use the official Python image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    build-essential \  
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Install `uv` package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using `uv`
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync


# Copy application code
COPY . .

# Create data directory
RUN mkdir -p .data/uploads .data/temp .logs

# Expose the port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]