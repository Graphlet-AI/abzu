#!/bin/bash

# This script provides a consistent interface for Docker Compose commands
# It automatically detects whether to use 'docker compose' or 'docker-compose'

# Function to detect the appropriate docker-compose command
detect_docker_compose() {
    # Check for docker compose (newer versions)
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo "docker compose"
        return 0
    fi

    # Check for docker-compose (older versions)
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
        return 0
    fi

    # If neither is found, return error
    echo "Error: Neither 'docker compose' nor 'docker-compose' found in PATH" >&2
    return 1
}

# Get the appropriate docker-compose command
DOCKER_COMPOSE_CMD=$(detect_docker_compose)

# If no command was found, exit with error
if [ $? -ne 0 ]; then
    exit 1
fi

# Execute the command with all arguments
$DOCKER_COMPOSE_CMD "$@" 