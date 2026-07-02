#!/bin/sh

set -eu

XDG_RUNTIME_DIR="/run/user/$(id -u)"
DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
QT_QPA_PLATFORM="wayland"

export XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS WAYLAND_DISPLAY QT_QPA_PLATFORM

if [ ! -S "${XDG_RUNTIME_DIR}/bus" ]; then
  echo "D-Bus session bus not found: ${XDG_RUNTIME_DIR}/bus" >&2
  exit 1
fi

if ! command -v kscreen-doctor >/dev/null 2>&1; then
  echo "kscreen-doctor is not installed or not in PATH" >&2
  exit 127
fi

exec kscreen-doctor --dpms on
