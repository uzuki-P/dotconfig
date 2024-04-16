#!/usr/bin/env bash

memory()
{
  TYPE="${BLOCK_INSTANCE:-mem}"

  awk -v type=$TYPE '
  /^MemTotal:/ {
    mem_total=$2
  }
  /^MemFree:/ {
    mem_free=$2
  }
  /^Buffers:/ {
    mem_free+=$2
  }
  /^Cached:/ {
    mem_free+=$2
  }
  /^SwapTotal:/ {
    swap_total=$2
  }
  /^SwapFree:/ {
    swap_free=$2
  }
  END {
    if (type == "swap") {
      free=swap_free/1024/1024
      used=(swap_total-swap_free)/1024/1024
      total=swap_total/1024/1024
    } else {
      free=mem_free/1024/1024
      used=(mem_total-mem_free)/1024/1024
      total=mem_total/1024/1024
    }

    pct=0
    if (total > 0) {
      pct=used/total*100
    }

    # full text
    # printf("%.1fG/%.1fG (%.f%%)\n", used, total, pct)

    # short text
    #printf("%02.f%%\n", pct)
    printf("%1.0f GB", used)

    # color
    if (pct > 90) {
      print("#FF0000")
    } else if (pct > 80) {
      print("#FFAE00")
    } else if (pct > 70) {
      print("#FFF600")
    }
  }
  ' /proc/meminfo
}

disk () {
  DIR="$HOME"
  ALERT_LOW="10" # color will turn red under this value (default: 10%)

  LOCAL_FLAG="-l"
  #LOCAL_FLAG="-l"
  #if [ "$1" = "-n" ] || [ "$2" = "-n" ]; then
  #    LOCAL_FLAG=""
  #fi

  df -h -P $LOCAL_FLAG "$DIR" | awk -v label="$LABEL" -v alert_low=$ALERT_LOW '
  /\/.*/ {
    # full text
    #print label $4

    # short text
    print label $4

    use=$5

    # no need to continue parsing
    exit 0
  }

  END {
    gsub(/%$/,"",use)
    if (100 - use < alert_low) {
      # color
      print "#FF0000"
    }
  }
  '
}

while true
do
  MEM=$(memory)
  #DISK=$(disk)
  
  DATA=""
  DATA+="| A | MEM $MEM | | |"
  #DATA+="| C | DISK $DISK | | |"
  # DATA+="| C | BATT $BATT% | | |"

  qdbus org.kde.plasma.doityourselfbar /id_17 \
    org.kde.plasma.doityourselfbar.pass "$DATA"

  sleep 3s
done

