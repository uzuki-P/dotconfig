#!/usr/bin/env bash
# Rebuilds the fixture APKs for test_server.py with the Android SDK's aapt2.
# Usage: ANDROID_SDK=~/Android/Sdk ./build.sh   (run from this directory)
set -euo pipefail
sdk="${ANDROID_SDK:-${HOME}/Android/Sdk}"
aapt2="$(ls -d "${sdk}"/build-tools/*/ | sort -V | tail -1)aapt2"
android_jar="$(ls -d "${sdk}"/platforms/android-*/ | sort -V | tail -1)android.jar"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

manifest() {
  cat >"$1" <<XML
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.$2">
  <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="35"/>
  <application android:icon="@mipmap/ic_launcher" android:label="$2"/>
</manifest>
XML
}

# Adaptive icon: a color background (with a night variant to ignore) and a vector
# foreground with a solid path, a gradient path, and a group transform.
a="${work}/adaptive"
mkdir -p "${a}/res/mipmap-anydpi-v26" "${a}/res/drawable" "${a}/res/values" "${a}/res/values-night"
manifest "${a}/AndroidManifest.xml" adaptive
cat >"${a}/res/values/colors.xml" <<'XML'
<resources><color name="icon_bg">#FF2E7D32</color><color name="mark">#FFFFFFFF</color></resources>
XML
cat >"${a}/res/values-night/colors.xml" <<'XML'
<resources><color name="icon_bg">#FF000000</color></resources>
XML
cat >"${a}/res/mipmap-anydpi-v26/ic_launcher.xml" <<'XML'
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
  <background android:drawable="@color/icon_bg"/>
  <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
XML
cat >"${a}/res/drawable/ic_launcher_foreground.xml" <<'XML'
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
  <path android:fillColor="@color/mark" android:pathData="M36,36h36v18h-36z"/>
  <group android:translateX="0" android:translateY="20">
    <path android:pathData="M36,40h36v12h-36z">
      <aapt:attr name="android:fillColor">
        <gradient android:type="linear" android:startX="36" android:startY="0" android:endX="72" android:endY="0"
            android:startColor="#FFFFEB3B" android:endColor="#FFFF5722"/>
      </aapt:attr>
    </path>
  </group>
</vector>
XML
"${aapt2}" compile --dir "${a}/res" -o "${work}/adaptive.zip"
"${aapt2}" link -I "${android_jar}" --manifest "${a}/AndroidManifest.xml" -o "${work}/adaptive-raw.apk" "${work}/adaptive.zip"
"${aapt2}" optimize --shorten-resource-paths --enable-sparse-encoding -o adaptive.apk "${work}/adaptive-raw.apk"

# Bitmap icon: PNGs at two densities; the denser one (blue) must win.
b="${work}/bitmap"
mkdir -p "${b}/res/mipmap-mdpi" "${b}/res/mipmap-xxxhdpi"
manifest "${b}/AndroidManifest.xml" bitmap
python3 -I - "${b}" <<'PY'
import sys
from PIL import Image
Image.new("RGB", (48, 48), (220, 0, 0)).save(f"{sys.argv[1]}/res/mipmap-mdpi/ic_launcher.png")
Image.new("RGB", (192, 192), (0, 0, 220)).save(f"{sys.argv[1]}/res/mipmap-xxxhdpi/ic_launcher.png")
PY
"${aapt2}" compile --dir "${b}/res" -o "${work}/bitmap.zip"
"${aapt2}" link -I "${android_jar}" --manifest "${b}/AndroidManifest.xml" -o bitmap.apk "${work}/bitmap.zip"
ls -l adaptive.apk bitmap.apk
