# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    SPARK_HOME=/opt/spark \
    PATH=$PATH:$SPARK_HOME/bin

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    default-jdk \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Spark (without Hadoop)
RUN cd /tmp && \
    # Download Spark
    wget https://archive.apache.org/dist/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3.tgz && \
    wget https://archive.apache.org/dist/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3.tgz.asc && \
    wget https://archive.apache.org/dist/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3.tgz.sha512 && \
    # Download and import Apache keys
    wget https://downloads.apache.org/spark/KEYS && \
    gpg --import KEYS && \
    # Verify signature
    gpg --verify spark-3.5.5-bin-hadoop3.tgz.asc spark-3.5.5-bin-hadoop3.tgz && \
    # Verify checksum
    echo "$(cat spark-3.5.5-bin-hadoop3.tgz.sha512 | cut -d' ' -f1) spark-3.5.5-bin-hadoop3.tgz" | sha512sum -c - && \
    # Extract and install
    tar xzf spark-3.5.5-bin-hadoop3.tgz && \
    mv spark-3.5.5-bin-hadoop3 /opt/spark && \
    # Cleanup
    rm -rf /tmp/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Install the package in development mode
RUN poetry install --no-interaction --no-ansi

# Create data directory
RUN mkdir -p data

# Set default command
CMD ["tail", "-f", "/dev/null"] 