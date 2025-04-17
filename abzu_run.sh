#!/bin/bash

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY environment variable is not set."
    echo "Please set it with:"
    echo "  export GEMINI_API_KEY=your_api_key"
    exit 1
fi

# Check if OPENAI_API_KEY is needed and set
if grep -q "OPENAI_API_KEY" /Users/rjurney/Software/abzu/baml_src/clients.baml; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "Warning: OPENAI_API_KEY environment variable is not set."
        echo "Some fallback features may not work."
    fi
fi

# Run the abzu command with passed arguments
poetry run abzu "$@"