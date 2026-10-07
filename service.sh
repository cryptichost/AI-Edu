#!/bin/bash

# Paths
VENV_PATH="./.venv/bin/activate"
PY_SCRIPT="main.py"

# PID files
NPM_PID_FILE="npm.pid"
PY_PID_FILE="python.pid"

case "$1" in
  start)
    echo "Starting Python..."
    source $VENV_PATH
    nohup python "$PY_SCRIPT" &
    echo $! > "$PY_PID_FILE"
    ;;

  stop)
    echo "Stopping Python..."
    if [ -f "$PY_PID_FILE" ]; then
      kill "$(cat $PY_PID_FILE)"
      rm "$PY_PID_FILE"
    fi
    
    ;;

  *)
    echo "Usage: ./service.sh {start|stop}"
    ;;
esac
