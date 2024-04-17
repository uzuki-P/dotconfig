#!/usr/bin/env bash

ID=$1

function default_interface {
  ip route | awk '/^default via/ {print $5; exit}'
}

iface=$(default_interface)
dt="1"
unit="MB"

function check_proc_net_dev {
    if [ ! -f "/proc/net/dev" ]; then
        echo "/proc/net/dev not found"
        exit 1
    fi
}

check_proc_net_dev

iface="${iface:-$(default_interface)}"
while [ -z "$iface" ]; do
    echo No default interface
    sleep "$dt"
    iface=$(default_interface)
done

case "$unit" in
    Kb|Kbit|Kbits)   bytes_per_unit=$((1024 / 8));;
    KB|KByte|KBytes) bytes_per_unit=$((1024));;
    Mb|Mbit|Mbits)   bytes_per_unit=$((1024 * 1024 / 8));;
    MB|MByte|MBytes) bytes_per_unit=$((1024 * 1024));;
    Gb|Gbit|Gbits)   bytes_per_unit=$((1024 * 1024 * 1024 / 8));;
    GB|GByte|GBytes) bytes_per_unit=$((1024 * 1024 * 1024));;
    Tb|Tbit|Tbits)   bytes_per_unit=$((1024 * 1024 * 1024 * 1024 / 8));;
    TB|TByte|TBytes) bytes_per_unit=$((1024 * 1024 * 1024 * 1024));;
    *) echo Bad unit "$unit" && exit 1;;
esac

scalar=$((bytes_per_unit * dt))
init_line=$(cat /proc/net/dev | grep "^[ ]*$iface:")
if [ -z "$init_line" ]; then
    echo Interface not found in /proc/net/dev: "$iface"
    exit 1
fi

init_received=$(awk '{print $2}' <<< $init_line)
init_sent=$(awk '{print $10}' <<< $init_line)

(while true; do cat /proc/net/dev; sleep "$dt"; done) |\
    stdbuf -oL grep "^[ ]*$iface:" |\
    awk -v scalar="$scalar" -v unit="$unit" -v iface="$iface" -v ids="$ID" '
BEGIN{old_received='"$init_received"';old_sent='"$init_sent"'}
{
  received=$2
  sent=$10
  rx=(received-old_received)/scalar;
  wx=(sent-old_sent)/scalar;
  tx=rx+wr;
  old_received=received;
  old_sent=sent;
  if(rx >= 0 && wx >= 0){
    format=sprintf("%.2f/%.2f %s/s\n", rx, wx, unit);
    system("qdbus org.kde.plasma.doityourselfbar /id_"ids" org.kde.plasma.doityourselfbar.pass \"| C | "format" | Network "iface" (Download/Upload) | |\"");

    fflush(stdout);
  }
}
'
