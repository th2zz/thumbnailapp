#!/bin/bash
# This is the script to run our app, the following args will be accepted and past to uvicorn
# --workers, --host, --port
APP_ROOT=app_root
set -e
POSITIONAL_ARGS=()
echo $@
echo "Activating virtual environment..."
. /${APP_ROOT}/.venv/bin/activate

while [[ $# -gt 0 ]]; do
  case $1 in
    -w|--workers)
      WORKERS="$2"
      shift 2
      # shift past argument and value
      ;;
    -h|--host)
      HOST="$2"
      shift 2
      # shift past argument and value
      ;;
    -p|--port)
      PORT="$2"
      shift 2
      # shift past argument and value
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done
set -- "${POSITIONAL_ARGS[@]}" # restore positional args

echo "workers ${WORKERS} host ${HOST} port ${PORT}"
exec uvicorn --workers ${WORKERS} --host ${HOST} --port ${PORT} app.main:app
