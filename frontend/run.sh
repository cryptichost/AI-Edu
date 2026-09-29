http-server dist -a 0.0.0.0 -p 80 --proxy http://localhost:8000 &
SERVER_PID=$!

cleanup() {
    kill -SIGTERM "$SERVER_PID"
    wait "$SERVER_PID"
    exit 0
}

trap cleanup SIGTERM

wait "$SERVER_PID"