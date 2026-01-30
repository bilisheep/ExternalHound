#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log()  { printf '[bootstrap] %s\n' "$*"; }
warn() { printf '[bootstrap][warn] %s\n' "$*" >&2; }
die()  { printf '[bootstrap][error] %s\n' "$*" >&2; exit 1; }

trap 'die "Command failed (line $LINENO): $BASH_COMMAND"' ERR

# Load optional env files to override defaults (if present)
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi
if [[ -f "$ROOT/backend/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/backend/.env"
  set +a
fi

# Defaults (can be overridden by env or .env)
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-externalhound_pg_pass}"
POSTGRES_DB="${POSTGRES_DB:-externalhound}"

NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-externalhound_neo4j_pass}"

MINIO_ROOT_USER="${MINIO_ROOT_USER:-admin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-externalhound_minio_pass}"
MINIO_BUCKET="${MINIO_BUCKET:-externalhound}"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-externalhound-postgres}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-externalhound-neo4j}"
MINIO_CONTAINER="${MINIO_CONTAINER:-externalhound-minio}"
REDIS_CONTAINER="${REDIS_CONTAINER:-externalhound-redis}"
NETWORK_NAME="${NETWORK_NAME:-externalhound-network}"

HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-180}"

COMPOSE=()

detect_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
  else
    die "Docker Compose not found. Install Docker Desktop or docker-compose."
  fi
}

check_prereqs() {
  command -v docker >/dev/null 2>&1 || die "Docker not found."
  docker info >/dev/null 2>&1 || die "Docker daemon not running."
  detect_compose
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  elif command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$port" 2>/dev/null | tail -n +2 | grep -q .
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -E "[:.]$port$" >/dev/null
  else
    return 2
  fi
}

check_ports() {
  if [[ "${SKIP_PORT_CHECK:-0}" == "1" ]]; then
    warn "Skipping port check (SKIP_PORT_CHECK=1)."
    return 0
  fi

  local ports=(5432 7474 7687 9000 9001 6379)
  for p in "${ports[@]}"; do
    if port_in_use "$p"; then
      die "Port $p is already in use. Stop the process or set SKIP_PORT_CHECK=1."
    elif [[ $? -eq 2 ]]; then
      warn "No tool to check ports; skipping check for $p."
    fi
  done
}

copy_if_missing() {
  local src="$1" dst="$2"
  if [[ -f "$dst" ]]; then
    log "Config exists: $dst"
  elif [[ -f "$src" ]]; then
    cp "$src" "$dst"
    log "Copied template: $src -> $dst"
  else
    warn "Template missing: $src (skipped)"
  fi
}

copy_templates() {
  # Backend: Always create config.toml as primary config source
  copy_if_missing "$ROOT/backend/config.example.toml" "$ROOT/backend/config.toml"

  # Frontend: Always create .env
  copy_if_missing "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"

  # Optional: Root .env (for docker-compose variable interpolation)
  # Only copy if USE_ENV=1 is set
  if [[ "${USE_ENV:-0}" == "1" && -f "$ROOT/.env.example" ]]; then
    copy_if_missing "$ROOT/.env.example" "$ROOT/.env"
  fi

  # Optional: Backend .env (for overriding specific config items)
  # Only copy if USE_BACKEND_ENV=1 is set
  if [[ "${USE_BACKEND_ENV:-0}" == "1" && -f "$ROOT/backend/.env.example" ]]; then
    copy_if_missing "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  fi
}

compose_up() {
  log "Starting Docker Compose services..."
  (cd "$ROOT" && "${COMPOSE[@]}" up -d)
}

wait_for_health() {
  local name="$1"
  local timeout="$2"
  local start_ts
  start_ts="$(date +%s)"

  while true; do
    local status
    status="$(docker inspect --format '{{.State.Health.Status}}' "$name" 2>/dev/null || true)"
    if [[ "$status" == "healthy" ]]; then
      log "Healthy: $name"
      return 0
    fi

    if [[ -z "$status" ]]; then
      local running
      running="$(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null || true)"
      if [[ "$running" == "true" ]]; then
        log "Running (no healthcheck): $name"
        return 0
      fi
    fi

    local now_ts
    now_ts="$(date +%s)"
    if (( now_ts - start_ts > timeout )); then
      warn "Health check timeout for $name"
      docker logs "$name" --tail 50 || true
      return 1
    fi
    sleep 2
  done
}

verify_postgres() {
  log "Verifying PostgreSQL initialization..."
  local result
  result="$(docker exec -i "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='tags';" \
    | tr -d '[:space:]' || true)"
  if [[ "$result" != "1" ]]; then
    die "PostgreSQL init check failed (table 'tags' missing)."
  fi
}

verify_neo4j() {
  log "Verifying Neo4j initialization..."

  # First, apply the initialization script if not already applied
  if ! docker exec -i "$NEO4J_CONTAINER" \
    cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "SHOW CONSTRAINTS;" 2>/dev/null | grep -q "external_id"; then

    log "Applying Neo4j initialization script..."
    docker exec -i "$NEO4J_CONTAINER" \
      cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
      < "$ROOT/db/init/neo4j/init.cypher" >/dev/null
    log "Neo4j initialization complete."
  else
    log "Neo4j already initialized."
  fi

  # Verify constraints exist
  docker exec -i "$NEO4J_CONTAINER" \
    cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "SHOW CONSTRAINTS;" >/dev/null
}

create_minio_bucket() {
  log "Ensuring MinIO bucket exists: $MINIO_BUCKET"
  docker run --rm \
    --network "$NETWORK_NAME" \
    -e "MC_HOST_local=http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@minio:9000" \
    minio/mc mb --ignore-existing "local/${MINIO_BUCKET}" >/dev/null
}

print_summary() {
  cat <<EOF

✅ ExternalHound Bootstrap Complete!

Services are ready:

PostgreSQL  : localhost:5432 (user: $POSTGRES_USER, db: $POSTGRES_DB)
Neo4j       : http://localhost:7474 (user: $NEO4J_USER)
MinIO API   : http://localhost:9000
MinIO UI    : http://localhost:9001 (user: $MINIO_ROOT_USER)
Redis       : localhost:6379

Next steps:
1) Backend:  cd backend && uvicorn app.main:app --reload --port 8000
2) Frontend: cd frontend && npm install && npm run dev
3) API docs: http://localhost:8000/docs
4) App UI:   http://localhost:5173

Configuration:
- Backend config: backend/config.toml (copied from config.example.toml)
- Frontend config: frontend/.env (copied from .env.example)
- See backend/CONFIG.md for detailed configuration documentation

EOF
}

main() {
  log "ExternalHound Bootstrap started..."
  check_prereqs
  check_ports
  copy_templates
  compose_up

  log "Waiting for services to become healthy..."
  wait_for_health "$POSTGRES_CONTAINER" "$HEALTH_TIMEOUT"
  wait_for_health "$NEO4J_CONTAINER" "$HEALTH_TIMEOUT"
  wait_for_health "$MINIO_CONTAINER" "$HEALTH_TIMEOUT"
  wait_for_health "$REDIS_CONTAINER" "$HEALTH_TIMEOUT"

  verify_postgres
  verify_neo4j
  create_minio_bucket

  print_summary
}

main "$@"
