# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Update package lists and install curl
RUN apt-get update && apt-get install -y curl

# Copy the requirements file into the container

# Install tuv package manager
RUN pip install uv

# Copy the rest of your application code into the container
COPY pyproject.toml uv.lock .

# Install the dependencies
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync --locked

COPY . .

# Set the working directory to the src directory
WORKDIR /app/src

# Set the default command for the container
CMD ["uv", "run", "main.py"]