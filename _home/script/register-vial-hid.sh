#!/bin/sh

set -eu

USER_GID="$(id -g)"
export USER_GID

sudo --preserve-env=USER_GID sh -c 'cat > /etc/udev/rules.d/59-vial.rules <<EOF
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{serial}=="*vial:f64c2b3c*", MODE="0660", GROUP="$USER_GID", TAG+="uaccess", TAG+="udev-acl"
EOF
udevadm control --reload
udevadm trigger'
