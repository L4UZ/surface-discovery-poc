#!/bin/sh
set -e

# Surface Discovery Docker Entrypoint Script
# Handles input processing and output directory management

# If first argument is a flag or help, run CLI directly
if [ "${1#-}" != "$1" ] || [ "$1" = "help" ] || [ "$1" = "--help" ]; then
    exec python cli.py "$@"
fi

# If first argument doesn't start with -, assume it's a URL
# and construct the full command
if [ "${1#-}" = "$1" ] && [ -n "$1" ]; then
    # URL provided as first argument
    URL="$1"
    shift

    # Default output file in /output directory
    OUTPUT_FILE="${OUTPUT_FILE:-/output/discovery_results.json}"

    # Build command
    CMD="python cli.py --url $URL --output $OUTPUT_FILE"

    # Add any additional arguments
    while [ $# -gt 0 ]; do
        CMD="$CMD $1"
        shift
    done

    echo "Running: $CMD"
    exec sh -c "$CMD"
fi

# Otherwise, execute whatever was passed
exec "$@"
