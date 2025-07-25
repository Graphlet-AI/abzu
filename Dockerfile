# Multi-stage build for better caching and faster iteration
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    wget \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Stage 1: Install Poetry
FROM base AS poetry-installer

RUN curl -sSL https://install.python-poetry.org | python3 -

# Stage 2: Build dependencies
FROM base AS dependencies

# Build TA-Lib directly in this stage
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz && \
    ldconfig && \
    # Create symlinks for Python package (expects hyphen instead of underscore) \
    cd /usr/lib && \
    ln -sf libta_lib.so libta-lib.so && \
    ln -sf libta_lib.so.0 libta-lib.so.0 && \
    ln -sf libta_lib.a libta-lib.a && \
    echo "=== Checking TA-Lib installation ===" && \
    ls -la /usr/lib/libta*lib* && \
    echo "=== ldconfig output ===" && \
    ldconfig -p | grep "ta.lib"

# Copy Poetry from installer stage
COPY --from=poetry-installer /opt/poetry /opt/poetry

# Set working directory
WORKDIR /app

# Copy only dependency files for caching
COPY pyproject.toml poetry.lock* ./

# First, install all dependencies except ta-lib
RUN cp pyproject.toml pyproject.toml.orig && \
    sed -i '/ta-lib/d' pyproject.toml && \
    poetry lock && \
    poetry install --no-interaction --no-ansi --no-root && \
    mv pyproject.toml.orig pyproject.toml

# Install ta-lib Python package with proper environment
ENV TA_INCLUDE_PATH="/usr/include" \
    TA_LIBRARY_PATH="/usr/lib" \
    LD_LIBRARY_PATH="/usr/lib:$LD_LIBRARY_PATH"

RUN pip install numpy && \
    pip install ta-lib==0.6.4 && \
    # Regenerate lock file with full dependencies including ta-lib
    poetry lock

# Stage 3: Final application image
FROM dependencies AS final

# Copy application code
COPY . .

# Copy the lock file from dependencies stage (it has ta-lib properly included)
COPY --from=dependencies /app/poetry.lock ./

# Install the project itself (in editable mode)
RUN poetry install --no-interaction --no-ansi --only-root

# Generate BAML client code if baml is available
RUN poetry run baml generate || echo "BAML generation skipped"

# Create data directory
RUN mkdir -p data

# Set default command
CMD ["tail", "-f", "/dev/null"]
