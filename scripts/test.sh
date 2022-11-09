#!/bin/sh
# This is the script to run all tests
set -e
APP_ROOT=app_root
echo "Activating virtual environment..."
. /${APP_ROOT}/.venv/bin/activate
echo "Start running pytest..."
pytest "$@"
