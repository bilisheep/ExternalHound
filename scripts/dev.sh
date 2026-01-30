#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log()  { printf '[dev] %s\n' "$*"; }
warn() { printf '[dev][warn] %s\n' "$*" >&2; }
die()  { printf '[dev][error] %s\n' "$*" >&2; exit 1; }

trap 'cleanup' EXIT INT TERM

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  log "Stopping services..."
  if [[ -n "$BACKEND_PID" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    log "Backend stopped (PID: $BACKEND_PID)"
  fi
  if [[ -n "$FRONTEND_PID" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    log "Frontend stopped (PID: $FRONTEND_PID)"
  fi
}

check_docker_services() {
  log "Checking Docker services..."

  local containers=(
    "externalhound-postgres"
    "externalhound-neo4j"
    "externalhound-minio"
    "externalhound-redis"
  )

  for container in "${containers[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
      die "Docker container not running: $container. Run './scripts/bootstrap.sh' first."
    fi
  done

  log "Docker services are running."
}

check_configs() {
  log "Checking configuration files..."

  if [[ ! -f "$ROOT/backend/config.toml" && ! -f "$ROOT/backend/.env" ]]; then
    warn "No backend config found. Creating from template..."
    if [[ -f "$ROOT/backend/config.example.toml" ]]; then
      cp "$ROOT/backend/config.example.toml" "$ROOT/backend/config.toml"
      log "Created backend/config.toml"
    else
      die "backend/config.example.toml not found. Run './scripts/bootstrap.sh' first."
    fi
  fi

  if [[ ! -f "$ROOT/frontend/.env" ]]; then
    warn "No frontend config found. Creating from template..."
    if [[ -f "$ROOT/frontend/.env.example" ]]; then
      cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
      log "Created frontend/.env"
    else
      die "frontend/.env.example not found. Run './scripts/bootstrap.sh' first."
    fi
  fi
}

install_backend_deps() {
  log "Installing backend dependencies..."
  cd "$ROOT/backend"

  if [[ ! -d .venv ]]; then
    log "Creating Python virtual environment..."
    python3 -m venv .venv
  fi

  source .venv/bin/activate
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  log "Backend dependencies installed."
}

run_migrations() {
  log "Running database migrations..."
  cd "$ROOT/backend"
  source .venv/bin/activate

  # Check if migrations need to run
  if alembic current 2>/dev/null | grep -q "head"; then
    log "Database is up to date."
  else
    log "Applying migrations..."
    alembic upgrade head
    log "Migrations completed."
  fi
}

install_frontend_deps() {
  log "Installing frontend dependencies..."
  cd "$ROOT/frontend"

  if [[ ! -d node_modules ]]; then
    log "Running npm install..."
    npm install
  else
    log "Frontend dependencies already installed."
  fi
}

start_backend() {
  log "Starting backend server (http://localhost:8000)..."
  cd "$ROOT/backend"
  source .venv/bin/activate

  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$ROOT/backend.log" 2>&1 &
  BACKEND_PID=$!

  # Wait for backend to be ready
  local max_wait=30
  local waited=0
  while ! curl -s http://localhost:8000/health >/dev/null 2>&1; do
    if (( waited >= max_wait )); then
      warn "Backend health check timeout. Check backend.log for errors."
      break
    fi
    sleep 1
    ((waited++))
  done

  log "Backend started (PID: $BACKEND_PID)"
  log "Backend logs: $ROOT/backend.log"
  log "API docs: http://localhost:8000/docs"
}

start_frontend() {
  log "Starting frontend server (http://localhost:5173)..."
  cd "$ROOT/frontend"

  npm run dev > "$ROOT/frontend.log" 2>&1 &
  FRONTEND_PID=$!

  # Wait for frontend to be ready
  local max_wait=30
  local waited=0
  while ! curl -s http://localhost:5173 >/dev/null 2>&1; do
    if (( waited >= max_wait )); then
      warn "Frontend health check timeout. Check frontend.log for errors."
      break
    fi
    sleep 1
    ((waited++))
  done

  log "Frontend started (PID: $FRONTEND_PID)"
  log "Frontend logs: $ROOT/frontend.log"
}

print_info() {
  cat <<EOF

✅ Development environment is ready!

Services:
  Frontend    : http://localhost:5173
  Backend API : http://localhost:8000
  API Docs    : http://localhost:8000/docs

Logs:
  Backend  : tail -f $ROOT/backend.log
  Frontend : tail -f $ROOT/frontend.log

Docker Services:
  PostgreSQL  : localhost:5432
  Neo4j       : http://localhost:7474
  MinIO       : http://localhost:9001
  Redis       : localhost:6379

Press Ctrl+C to stop all services.

EOF
}

wait_forever() {
  log "Services are running. Press Ctrl+C to stop."
  while true; do
    # Check if processes are still running
    if [[ -n "$BACKEND_PID" ]] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      warn "Backend process died unexpectedly. Check backend.log"
      exit 1
    fi
    if [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
      warn "Frontend process died unexpectedly. Check frontend.log"
      exit 1
    fi
    sleep 5
  done
}

main() {
  log "Starting ExternalHound development environment..."

  check_docker_services
  check_configs
  install_backend_deps
  run_migrations
  install_frontend_deps
  start_backend
  sleep 2  # Give backend time to start
  start_frontend

  print_info
  wait_forever
}

main "$@"
