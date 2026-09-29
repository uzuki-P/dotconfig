#!/bin/sh

exec /home/uzuki_p/Android/Sdk/emulator/emulator \
  -avd Spendr_Headless_API_36 \
  -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect "$@"
