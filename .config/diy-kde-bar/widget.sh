#!/usr/bin/env bash

ID=$1

while true
do
  MEM=$(/home/uzuki_p/.config/diy-kde-bar/script/memory.sh)
  TEMP=$(sensors | grep "^[ ]*CPU" | awk '{print substr($2,2)}')
  # DISK=$(df -h -P "$HOME" | awk '/\/.*/ { print $5 }')
  
  DATA=""
  # DATA+="| A | $DISK | Home Storage Used | |"
  DATA+="| A | $MEM | RAM Usage | |"
  DATA+="| A | $TEMP | CPU Temp | |"

  qdbus org.kde.plasma.doityourselfbar /id_$ID \
    org.kde.plasma.doityourselfbar.pass "$DATA"

  sleep 3s
done

