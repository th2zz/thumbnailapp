#!/bin/bash
set -e
POSITIONAL_ARGS=()
echo $@
echo "Activating virtual environment..."
. /application_root/.venv/bin/activate

while [[ $# -gt 0 ]]; do
  case $1 in
    -w|--workers)
      WORKERS="$2"
      shift 2 # past argument
      # shift # past value
      ;;
    -h|--host)
      HOST="$2"
      shift 2 # past argument
      # shift # past value
      ;;
    -p|--port)
      PORT="$2"
      shift 2 # past argument
      # shift # past value
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
set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

# echo "workers ${WORKERS} host ${HOST} port ${PORT}"
exec uvicorn --workers ${WORKERS} --host ${HOST} --port ${PORT} app.main:app
