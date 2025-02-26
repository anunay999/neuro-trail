# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container

# Install tuv package manager
RUN pip install uv

# Copy the rest of your application code into the container
COPY . .

# Install the dependencies
RUN uv sync


# Set the working directory to the src directory
WORKDIR /app/src

# Set the default command for the container
CMD ["uv", "run", "main.py"]