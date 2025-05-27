#!/bin/bash

# Exit on error
set -e

echo "Setting up development environment for Abzu..."

# Function to detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        *)          echo "unknown";;
    esac
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install docker-compose wrapper
install_docker_compose_wrapper() {
    local wrapper_path="$HOME/.local/bin/docker-compose-wrapper"
    local wrapper_dir="$(dirname "$wrapper_path")"

    # Create .local/bin if it doesn't exist
    mkdir -p "$wrapper_dir"

    # Copy the wrapper script
    cp "$(dirname "$0")/docker-compose-wrapper.sh" "$wrapper_path"
    chmod +x "$wrapper_path"

    # Add to PATH if not already present
    if [[ ":$PATH:" != *":$wrapper_dir:"* ]]; then
        if [ "$(detect_os)" = "macos" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
            export PATH="$HOME/.local/bin:$PATH"
        else
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            export PATH="$HOME/.local/bin:$PATH"
        fi
    fi

    # Return the full path to the wrapper
    echo "$wrapper_path"
}

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    OS="darwin"
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        ARCH="arm64"
    else
        ARCH="amd64"
    fi
    INSTALL_DIR="$HOME/.local/bin"
    SHELL_RC="$HOME/.zshrc"  # macOS typically uses zsh
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    OS="linux"
    ARCH="amd64"
    INSTALL_DIR="$HOME/.local/bin"
    SHELL_RC="$HOME/.bashrc"
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Check if Docker is installed
if ! command_exists docker; then
    echo "Docker is not installed. Please install Docker first."
    if [[ "$OS" == "darwin" ]]; then
        echo "For macOS, you can install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    else
        echo "For Linux, follow the instructions at: https://docs.docker.com/engine/install/"
    fi
    exit 1
fi

# Check if Docker Compose is available
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    if [[ "$OS" == "darwin" ]]; then
        echo "Docker Compose should be included with Docker Desktop for macOS."
    else
        echo "For Linux, follow the instructions at: https://docs.docker.com/compose/install/"
    fi
    exit 1
fi

# Create installation directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Install docker-compose wrapper and get its path
echo "Installing docker-compose wrapper..."
WRAPPER_PATH=$(install_docker_compose_wrapper)

# Install Taskfile
echo "Installing Taskfile..."
TASKFILE_VERSION="v3.36.0"  # You can update this to the latest version
TASKFILE_URL="https://github.com/go-task/task/releases/download/${TASKFILE_VERSION}/task_${OS}_${ARCH}.tar.gz"

# Download and install Taskfile
echo "Downloading Taskfile for ${OS}/${ARCH}..."
curl -sSL "$TASKFILE_URL" | tar xz -C "$INSTALL_DIR" task

# Make task executable
chmod +x "$INSTALL_DIR/task"

# Verify installation
if command_exists task; then
    echo "Taskfile installed successfully!"
    echo "Version: $(task --version)"
else
    echo "Taskfile installation failed. Please install manually."
    exit 1
fi

# Build Docker container using the full path to the wrapper
echo "Building Docker container..."
"$WRAPPER_PATH" build

echo "Setup complete!"
if [[ "$OS" == "darwin" ]]; then
    echo "Please run 'source $SHELL_RC' or restart your terminal to ensure Taskfile is in your PATH."
else
    echo "Please run 'source $SHELL_RC' or restart your terminal to ensure Taskfile is in your PATH."
fi
echo "You can then use 'task help' to see available commands." 