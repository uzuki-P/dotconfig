#!/bin/bash
# Headless Android emulator with Tailscale (adb-over-TCP) exposure.
#
# Runs as a systemd user service so it survives shell/SSH disconnects.
# Uses -gpu lavapipe (pure software renderer) because the default gfxstream
# backend crashes with Mesa 26 on this host.
#
# Usage:
#   emu-headless.sh start   [avd]   launch the emulator + Tailscale bridge (default AVD: Medium_Phone_API36)
#   emu-headless.sh stop            stop everything
#   emu-headless.sh status          show state, adb devices, and Tailscale IP
#   emu-headless.sh log             tail the emulator log
#   emu-headless.sh connect         print the adb connect command for remote machines

set -euo pipefail

AVD="${EMU_AVD:-Medium_Phone_API36}"
ADB_PORT=5555          # emulator's adb-over-TCP port (loopback)
BRIDGE_PORT=5556       # port exposed on the Tailscale interface
EMU_UNIT="android-emulator.service"
BRIDGE_UNIT="adb-tailscale-bridge.service"
EMU_LOG="/tmp/emu-lavapipe.log"
ADB="$HOME/Android/Sdk/platform-tools/adb"
EMU="$HOME/Android/Sdk/emulator/emulator"

tailscale_ip() { tailscale ip -4 2>/dev/null | head -1; }

enable_hardware_keyboard() {
  local avd="$1"
  local avd_home="${ANDROID_AVD_HOME:-$HOME/.android/avd}"
  local config="$avd_home/${avd}.avd/config.ini"

  if [ ! -f "$config" ]; then
    echo "error: AVD config not found: $config" >&2
    exit 1
  fi

  # Required for physical-key input forwarded by an ADB client such as scrcpy.
  if grep -q '^hw\.keyboard=' "$config"; then
    sed -i 's/^hw\.keyboard=.*/hw.keyboard=yes/' "$config"
  else
    echo 'hw.keyboard=yes' >> "$config"
  fi
}

start() {
  local avd="${1:-$AVD}"
  local ip; ip="$(tailscale_ip)"
  if [ -z "$ip" ]; then echo "error: tailscale not running"; exit 1; fi

  enable_hardware_keyboard "$avd"

  # 1. emulator
  if systemctl --user is-active --quiet "$EMU_UNIT"; then
    echo "emulator already running"
  else
    echo "starting emulator (avd=$avd, gpu=lavapipe)..."
    systemd-run --user --unit="$EMU_UNIT" --collect \
      env VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json \
          VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json \
          LIBGL_ALWAYS_SOFTWARE=1 \
      "$EMU" -avd "$avd" -no-window -no-audio -no-boot-anim -no-snapshot \
        -gpu lavapipe -camera-back none -camera-front none \
        -netdelay none -netspeed full > "$EMU_LOG" 2>&1
  fi

  # 2. wait for boot + enable adb-over-TCP
  echo "waiting for boot..."
  "$ADB" wait-for-device 2>/dev/null
  for _ in $(seq 1 60); do
    [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && break
    sleep 3
  done
  "$ADB" tcpip "$ADB_PORT" >/dev/null

  # 3. socat bridge: Tailscale IP -> emulator adb port
  if systemctl --user is-active --quiet "$BRIDGE_UNIT"; then
    echo "bridge already running"
  else
    echo "exposing adb on $ip:$BRIDGE_PORT..."
    systemd-run --user --unit="$BRIDGE_UNIT" --collect \
      socat "TCP-LISTEN:${BRIDGE_PORT},bind=${ip},fork,reuseaddr" "TCP:127.0.0.1:${ADB_PORT}"
  fi

  echo; echo "ready. From a Tailscale peer:"
  echo "  adb connect ${ip}:${BRIDGE_PORT}"
}

stop() {
  systemctl --user stop "$BRIDGE_UNIT" 2>/dev/null || true
  systemctl --user stop "$EMU_UNIT" 2>/dev/null || true
  "$ADB" emu kill 2>/dev/null || true
  echo "stopped"
}

status() {
  local ip; ip="$(tailscale_ip)"
  echo "emulator : $(systemctl --user is-active "$EMU_UNIT" 2>/dev/null || echo inactive)"
  echo "bridge   : $(systemctl --user is-active "$BRIDGE_UNIT" 2>/dev/null || echo inactive)"
  echo "tail IP  : ${ip:-N/A}"
  echo "adb connect ${ip:-<ip>}:${BRIDGE_PORT}"
  echo "--- devices ---"
  "$ADB" devices 2>/dev/null
}

log() { tail -n "${1:-40}" -f "$EMU_LOG" 2>/dev/null || echo "no log at $EMU_LOG"; }

connect() {
  local ip; ip="$(tailscale_ip)"
  echo "On a Tailscale-connected machine:"
  echo "  adb connect ${ip}:${BRIDGE_PORT}"
  echo "  scrcpy                    # optional screen mirror"
}

case "${1:-}" in
  start)   shift; start "$@" ;;
  stop)    stop ;;
  status)  status ;;
  log)     shift; log "$@" ;;
  connect) connect ;;
  *) echo "usage: $(basename "$0") {start [avd]|stop|status|log [n]|connect}"; exit 1 ;;
esac
