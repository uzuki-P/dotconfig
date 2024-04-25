#!/bin/sh

SDL_VIDEODRIVER=x11 \
  scrcpy -d \
  --video-bit-rate=10000000 \
  --turn-screen-off \
  --show-touches \
  --stay-awake \
  --window-borderless \
  --window-x=$((1920-390-4)) \
  --window-y=$((1080+4)) \
  --window-width=390 \
  # --window-height=700 \
  --no-audio
