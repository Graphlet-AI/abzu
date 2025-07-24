# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH=$PATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock* ./

# Copy the rest of the application (including README.md)
COPY . .

# Always regenerate the lock file to match pyproject.toml
RUN poetry lock && \
    poetry install --no-interaction --no-ansi

# List available scripts and try to find baml
RUN poetry run which baml || echo "baml not found" && \
    poetry run python -c "import baml; print(baml.__file__)" || echo "baml module not found" && \
    poetry run python -c "import baml_py; print(baml_py.__file__)" || echo "baml_py module not found"

# Generate BAML client code using Poetry
RUN poetry run baml generate

# Create data directory
RUN mkdir -p data

# Set default command
CMD ["tail", "-f", "/dev/null"]
