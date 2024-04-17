#!/usr/bin/env bash

ID=$1

while true
do
  MEM=$(/home/uzuki_p/.config/diy-kde-bar/script/memory.sh)
  #DISK=$(disk)
  
  DATA=""
  DATA+="| A | MEM $MEM | | |"
  #DATA+="| C | DISK $DISK | | |"
  # DATA+="| C | BATT $BATT% | | |"

  qdbus org.kde.plasma.doityourselfbar /id_$ID \
    org.kde.plasma.doityourselfbar.pass "$DATA"

  sleep 3s
done

