#!/usr/bin/env bash
# tests/cpu/service.sh
#
# Usage (from repo root):
#   chmod +x tests/cpu/service.sh
#   tests/cpu/service.sh up                  # start & wait until Chroma + Flask are healthy
#   tests/cpu/service.sh down                # stop & remove containers + volumes
#   tests/cpu/service.sh logs                # tail logs
#   tests/cpu/service.sh restart             # force recreate + wait healthy
#
# Options:
#   --compose-file <path>      (default: tests/cpu/docker-compose.yml)
#   --base-url <url>           (default: http://localhost:5000)      # Chromaviz UI base
#   --health-path <path>       (default: /heartbeat)                  # Chromaviz health path
#   --chroma-url <url>         (default: http://localhost:8000)       # Chroma API base
#   --chroma-health <path>     (default: /api/v2/heartbeat)           # Chroma health path
#   --wait-minutes <int>       (default: 5)
#
# This script matches the “no Nginx” compose setup:
# - ChromaDB API exposed at http://localhost:8000      (service: chroma)
# - Chromaviz Flask UI exposed at http://localhost:5000 (service: chromaviz)

set -Eeuo pipefail

ACTION="${1:-up}"
if [[ $# -gt 0 ]]; then shift || true; fi

COMPOSE_FILE="tests/cpu/docker-compose.yml"

# Chromaviz (Flask)
BASE_URL="http://localhost:5000"
HEALTH_PATH="/heartbeat"

# Chroma
CHROMA_URL="http://localhost:8000"
CHROMA_HEALTH="/api/v2/heartbeat"

WAIT_MINUTES=5

usage() {
  sed -n '1,60p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose-file)  COMPOSE_FILE="${2:?}"; shift 2 ;;
    --base-url)      BASE_URL="${2:?}";     shift 2 ;;
    --health-path)   HEALTH_PATH="${2:?}";  shift 2 ;;
    --chroma-url)    CHROMA_URL="${2:?}";   shift 2 ;;
    --chroma-health) CHROMA_HEALTH="${2:?}";shift 2 ;;
    --wait-minutes)  WAIT_MINUTES="${2:?}"; shift 2 ;;
    -h|--help)       usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

# Detect docker compose command
if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
elif docker-compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  echo "Error: Docker Compose not found (need 'docker compose' or 'docker-compose')." >&2
  exit 1
fi

COMPOSE="${COMPOSE_CMD} -f ${COMPOSE_FILE}"

http_ok() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    # Accept any 2xx response as healthy
    local code
    code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "$url" || true)"
    [[ "$code" =~ ^2 ]]
  elif command -v wget >/dev/null 2>&1; then
    # wget returns non-zero for non-2xx/3xx
    wget -q --timeout=5 -O /dev/null "$url"
  else
    echo "Error: need curl or wget installed for health checks." >&2
    return 1
  fi
}

wait_until_healthy() {
  local name="$1"
  local url="$2"
  echo "Waiting for ${name} to be healthy at ${url} ..."
  local deadline=$(( $(date +%s) + $WAIT_MINUTES*60 ))
  while (( $(date +%s) < deadline )); do
    if http_ok "$url"; then
      echo "${name} healthy."
      return 0
    fi
    sleep 3
  done
  echo "ERROR: ${name} did not become healthy within ${WAIT_MINUTES} minute(s). Last tried: ${url}" >&2
  return 1
}

FLASK_HEALTH_URL="${BASE_URL%/}${HEALTH_PATH}"
CHROMA_HEALTH_URL="${CHROMA_URL%/}${CHROMA_HEALTH}"

case "$ACTION" in
  up)
    eval "$COMPOSE up -d"
    # Backend first, then UI
    wait_until_healthy "ChromaDB API" "$CHROMA_HEALTH_URL"
    wait_until_healthy "Chromaviz (Flask)" "$FLASK_HEALTH_URL"
    echo
    echo "Ready."
    echo "Chroma API:   ${CHROMA_URL}"
    echo "Chromaviz UI: ${BASE_URL}"
    ;;
  restart)
    eval "$COMPOSE up -d --force-recreate"
    wait_until_healthy "ChromaDB API" "$CHROMA_HEALTH_URL"
    wait_until_healthy "Chromaviz (Flask)" "$FLASK_HEALTH_URL"
    echo
    echo "Restarted."
    echo "Chroma API:   ${CHROMA_URL}"
    echo "Chromaviz UI: ${BASE_URL}"
    ;;
  logs)
    eval "$COMPOSE logs -f"
    ;;
  down)
    eval "$COMPOSE down -v"
    echo "Service stopped and volumes removed."
    ;;
  *)
    echo "Unknown action: $ACTION" >&2
    usage
    ;;
esac







# #!/usr/bin/env bash
# # tests/cpu/service.sh
# #
# # Usage (from repo root):
# #   chmod +x tests/cpu/service.sh
# #   tests/cpu/service.sh up                  # start & wait until Chroma + Flask are healthy
# #   tests/cpu/service.sh down                # stop & remove containers + volumes
# #   tests/cpu/service.sh logs                # tail logs
# #   tests/cpu/service.sh restart             # force recreate + wait healthy
# #
# # Options:
# #   --compose-file <path>      (default: tests/cpu/docker-compose.yml)
# #   --base-url <url>           (default: http://localhost:5000)      # Chromaviz UI base
# #   --health-path <path>       (default: /heartbeat)                  # Chromaviz health path
# #   --chroma-url <url>         (default: http://localhost:8000)       # Chroma API base
# #   --chroma-health <path>     (default: /api/v2/heartbeat)           # Chroma health path
# #   --wait-minutes <int>       (default: 5)
# #
# # This script matches the “no Nginx” compose setup:
# # - ChromaDB API exposed at http://localhost:8000      (service: chroma)
# # - Chromaviz Flask UI exposed at http://localhost:5000 (service: chromaviz)

# set -Eeuo pipefail

# ACTION="${1:-up}"
# if [[ $# -gt 0 ]]; then shift || true; fi

# COMPOSE_FILE="tests/cpu/docker-compose.yml"

# # Chromaviz (Flask)
# BASE_URL="http://localhost:5000"
# HEALTH_PATH="/heartbeat"

# # Chroma
# CHROMA_URL="http://localhost:8000"
# CHROMA_HEALTH="/api/v2/heartbeat"

# WAIT_MINUTES=5

# usage() {
#   sed -n '1,60p' "$0" | sed 's/^# \{0,1\}//'
#   exit 1
# }

# while [[ $# -gt 0 ]]; do
#   case "$1" in
#     --compose-file)  COMPOSE_FILE="${2:?}"; shift 2 ;;
#     --base-url)      BASE_URL="${2:?}";     shift 2 ;;
#     --health-path)   HEALTH_PATH="${2:?}";  shift 2 ;;
#     --chroma-url)    CHROMA_URL="${2:?}";   shift 2 ;;
#     --chroma-health) CHROMA_HEALTH="${2:?}";shift 2 ;;
#     --wait-minutes)  WAIT_MINUTES="${2:?}"; shift 2 ;;
#     -h|--help)       usage ;;
#     *) echo "Unknown argument: $1" >&2; usage ;;
#   esac
# done

# # Detect docker compose command
# if docker compose version >/dev/null 2>&1; then
#   COMPOSE_CMD="docker compose"
# elif docker-compose version >/dev/null 2>&1; then
#   COMPOSE_CMD="docker-compose"
# else
#   echo "Error: Docker Compose not found (need 'docker compose' or 'docker-compose')." >&2
#   exit 1
# fi

# COMPOSE="${COMPOSE_CMD} -f ${COMPOSE_FILE}"

# http_ok() {
#   local url="$1"
#   if command -v curl >/dev/null 2>&1; then
#     # Accept any 2xx response as healthy
#     local code
#     code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "$url" || true)"
#     [[ "$code" =~ ^2 ]]
#   elif command -v wget >/dev/null 2>&1; then
#     # wget returns non-zero for non-2xx/3xx
#     wget -q --timeout=5 -O /dev/null "$url"
#   else
#     echo "Error: need curl or wget installed for health checks." >&2
#     return 1
#   fi
# }

# wait_until_healthy() {
#   local name="$1"
#   local url="$2"
#   echo "Waiting for ${name} to be healthy at ${url} ..."
#   local deadline=$(( $(date +%s) + $WAIT_MINUTES*60 ))
#   while (( $(date +%s) < deadline )); do
#     if http_ok "$url"; then
#       echo "${name} healthy."
#       return 0
#     fi
#     sleep 3
#   done
#   echo "ERROR: ${name} did not become healthy within ${WAIT_MINUTES} minute(s). Last tried: ${url}" >&2
#   return 1
# }

# FLASK_HEALTH_URL="${BASE_URL%/}${HEALTH_PATH}"
# CHROMA_HEALTH_URL="${CHROMA_URL%/}${CHROMA_HEALTH}"

# case "$ACTION" in
#   up)
#     eval "$COMPOSE up -d"
#     # Backend first, then UI
#     wait_until_healthy "ChromaDB API" "$CHROMA_HEALTH_URL"
#     wait_until_healthy "Chromaviz (Flask)" "$FLASK_HEALTH_URL"
#     echo
#     echo "Ready."
#     echo "Chroma API:   ${CHROMA_URL}"
#     echo "Chromaviz UI: ${BASE_URL}"
#     ;;
#   restart)
#     eval "$COMPOSE up -d --force-recreate"
#     wait_until_healthy "ChromaDB API" "$CHROMA_HEALTH_URL"
#     wait_until_healthy "Chromaviz (Flask)" "$FLASK_HEALTH_URL"
#     echo
#     echo "Restarted."
#     echo "Chroma API:   ${CHROMA_URL}"
#     echo "Chromaviz UI: ${BASE_URL}"
#     ;;
#   logs)
#     eval "$COMPOSE logs -f"
#     ;;
#   down)
#     eval "$COMPOSE down -v"
#     echo "Service stopped and volumes removed."
#     ;;
#   *)
#     echo "Unknown action: $ACTION" >&2
#     usage
#     ;;
# esac
