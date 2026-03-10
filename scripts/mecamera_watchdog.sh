#!/usr/bin/env bash
set -euo pipefail

SERVICE_ARG="${1:-auto}"
HEALTH_URL="${2:-http://127.0.0.1:8080/api/health}"
HEALTH_URL_FALLBACK_1="${HEALTH_URL_FALLBACK_1:-http://127.0.0.1:8080/api/status}"
HEALTH_URL_FALLBACK_2="${HEALTH_URL_FALLBACK_2:-http://127.0.0.1:8080/api/nanny-cam/status}"
HEALTH_URL_FALLBACK_3="${HEALTH_URL_FALLBACK_3:-http://127.0.0.1:8080/}"
STATE_DIR="/var/tmp"
STATE_FILE="${STATE_DIR}/mecamera_watchdog_failcount"
NET_STATE_FILE="${STATE_DIR}/mecamera_watchdog_netfailcount"
MAX_FAILS="${MAX_FAILS:-3}"
CURL_TIMEOUT="${CURL_TIMEOUT:-5}"
WIFI_IFACE="${WIFI_IFACE:-wlan0}"

detect_service_name() {
  # Prefer the actively running ME Camera unit if one exists.
  if systemctl is-active --quiet mecamera-lite 2>/dev/null; then
    echo "mecamera-lite"
    return
  fi

  if systemctl is-active --quiet mecamera 2>/dev/null; then
    echo "mecamera"
    return
  fi

  # Fall back to an installed unit when neither is currently active.
  if systemctl list-unit-files --type=service 2>/dev/null | grep -q '^mecamera-lite\.service'; then
    echo "mecamera-lite"
    return
  fi

  if systemctl list-unit-files --type=service 2>/dev/null | grep -q '^mecamera\.service'; then
    echo "mecamera"
    return
  fi

  echo "mecamera"
}

if [[ "${SERVICE_ARG}" == "auto" ]]; then
  SERVICE_NAME="$(detect_service_name)"
else
  SERVICE_NAME="${SERVICE_ARG}"
fi

if ! systemctl list-unit-files --type=service 2>/dev/null | grep -q "^${SERVICE_NAME}\.service"; then
  logger -t mecamera-watchdog "service ${SERVICE_NAME} is not installed; trying auto-detect fallback"
  SERVICE_NAME="$(detect_service_name)"
fi

mkdir -p "${STATE_DIR}"

fail_count=0
if [[ -f "${STATE_FILE}" ]]; then
  fail_count=$(cat "${STATE_FILE}" 2>/dev/null || echo "0")
fi

net_fail_count=0
if [[ -f "${NET_STATE_FILE}" ]]; then
  net_fail_count=$(cat "${NET_STATE_FILE}" 2>/dev/null || echo "0")
fi

if curl -fsS --max-time "${CURL_TIMEOUT}" "${HEALTH_URL}" >/dev/null 2>&1 || \
   curl -fsS --max-time "${CURL_TIMEOUT}" "${HEALTH_URL_FALLBACK_1}" >/dev/null 2>&1 || \
   curl -fsS --max-time "${CURL_TIMEOUT}" "${HEALTH_URL_FALLBACK_2}" >/dev/null 2>&1 || \
   curl -fsS --max-time "${CURL_TIMEOUT}" "${HEALTH_URL_FALLBACK_3}" >/dev/null 2>&1; then
  echo "0" > "${STATE_FILE}"
else
  fail_count=$((fail_count + 1))
  echo "${fail_count}" > "${STATE_FILE}"
  logger -t mecamera-watchdog "health check failed (${fail_count}/${MAX_FAILS}) for ${HEALTH_URL} (fallbacks attempted)"
fi

# Network sanity check (service can be healthy locally while Wi-Fi is disconnected)
have_ip=0
if ip -4 addr show "${WIFI_IFACE}" 2>/dev/null | grep -q "inet "; then
  have_ip=1
fi

gateway="$(ip route 2>/dev/null | awk '/^default/ {print $3; exit}')"
can_reach_gateway=0
if [[ -n "${gateway}" ]] && ping -c 1 -W 2 "${gateway}" >/dev/null 2>&1; then
  can_reach_gateway=1
fi

if [[ "${have_ip}" -eq 1 && "${can_reach_gateway}" -eq 1 ]]; then
  echo "0" > "${NET_STATE_FILE}"
else
  net_fail_count=$((net_fail_count + 1))
  echo "${net_fail_count}" > "${NET_STATE_FILE}"
  logger -t mecamera-watchdog "network check failed (${net_fail_count}/${MAX_FAILS}) iface=${WIFI_IFACE} ip=${have_ip} gw=${can_reach_gateway}"
fi

if (( fail_count >= MAX_FAILS )); then
  logger -t mecamera-watchdog "restarting ${SERVICE_NAME} after ${fail_count} failed checks"
  systemctl restart "${SERVICE_NAME}" >/dev/null 2>&1 || true
  echo "0" > "${STATE_FILE}"
fi

if (( net_fail_count >= MAX_FAILS )); then
  logger -t mecamera-watchdog "attempting Wi-Fi recovery on ${WIFI_IFACE} after ${net_fail_count} failed checks"
  iw dev "${WIFI_IFACE}" set power_save off >/dev/null 2>&1 || true
  wpa_cli -i "${WIFI_IFACE}" reconfigure >/dev/null 2>&1 || true
  wpa_cli -i "${WIFI_IFACE}" reconnect >/dev/null 2>&1 || true
  systemctl restart dhcpcd >/dev/null 2>&1 || true
  systemctl restart "${SERVICE_NAME}" >/dev/null 2>&1 || true
  echo "0" > "${NET_STATE_FILE}"
fi
