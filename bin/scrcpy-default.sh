#!/bin/sh

SDL_VIDEODRIVER=x11 \
  scrcpy -d \
  --video-bit-rate=5000000 \
  --turn-screen-off \
  --show-touches \
  --stay-awake \
  --window-borderless \
  --window-width=390 \
  --no-audio \
  --shortcut-mod="lalt,ralt"

