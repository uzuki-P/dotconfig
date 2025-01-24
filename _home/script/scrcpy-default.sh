#!/bin/sh

SDL_VIDEODRIVER=x11 \
  scrcpy \
  --video-bit-rate=2000000 \
  --max-size=720 \
  --turn-screen-off \
  --show-touches \
  --stay-awake \
  --window-borderless \
  --window-width=390 \
  --no-audio \
  --shortcut-mod="lalt,ralt"

