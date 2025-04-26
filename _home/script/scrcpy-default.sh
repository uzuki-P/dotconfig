#!/bin/sh

SDL_VIDEODRIVER=x11 \
  scrcpy \
  --video-bit-rate=6000000 \
  --max-size=720 \
  --turn-screen-off \
  --stay-awake \
  --window-borderless \
  --window-width=390 \
  --no-audio \
  --no-mouse-hover \
  --shortcut-mod="lalt,ralt"

# --show-touches \
