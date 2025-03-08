# Use the official Python image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install `uv` package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml  ./

# Install dependencies using `uv`
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync


# Copy application code
COPY . .


# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
ENTRYPOINT ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
