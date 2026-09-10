#!/bin/bash

# Paths
VENV_PATH="./.venv/bin/activate"
PY_SCRIPT="main.py"
NPM_DIR="./frontend-vue"

# PID files
NPM_PID_FILE="npm.pid"
PY_PID_FILE="python.pid"

case "$1" in
  start)
    echo "Starting npm..."
    nohup npm --prefix "$NPM_DIR" run dev > /dev/null 2>&1 &
    echo $! > "$NPM_PID_FILE"

    echo "Starting Python..."
    source "$VENV_PATH"
    nohup python "$PY_SCRIPT" &
    echo $! > "$PY_PID_FILE"

    echo "Both services started."
    ;;

  stop)
    echo "Stopping npm..."
    if [ -f "$NPM_PID_FILE" ]; then
      kill "$(cat $NPM_PID_FILE)"
      rm "$NPM_PID_FILE"
    fi

    echo "Stopping Python..."
    if [ -f "$PY_PID_FILE" ]; then
      kill "$(cat $PY_PID_FILE)"
      rm "$PY_PID_FILE"
    fi

    echo "Both services stopped."
    ;;

  *)
    echo "Usage: ./service.sh {start|stop}"
    ;;
esac
