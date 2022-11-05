#!/bin/sh

set -e

echo "Activating virtual environment..."
. /application_root/.venv/bin/activate
echo "Running pytest..."
pytest "$@"
