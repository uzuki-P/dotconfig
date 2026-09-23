# Vicinae emoji previews

Vicinae 0.29.0 uses its bundled Qt to draw emoji preview images. On this Fedora
install, that Qt build draws the system's `Noto-COLRv1.ttf` font as blank
images. The workaround gives only the Vicinae service a Fontconfig setup that
rejects that font and uses Google's Noto Color Emoji v2.048 font, which uses
the CBDT/CBLC format that Vicinae's bundled Qt can draw.

## Reinstall the workaround

From `~/dotconfig`, install the two saved config files. These commands create
symlinks on a clean install, keep identical files already in place, and refuse
to replace different ones:

```bash
link_config() {
  local source_file="$PWD/$1"
  local target_file="$HOME/$2"
  if [[ -L "$target_file" ]]; then
    [[ "$(readlink "$target_file")" == "$source_file" ]] && return 0
    printf 'Different symlink already exists: %s\n' "$target_file" >&2
    return 1
  fi
  if [[ -e "$target_file" ]]; then
    cmp -s "$source_file" "$target_file" && return 0
    printf 'Different config already exists: %s\n' "$target_file" >&2
    return 1
  fi
  mkdir -p "$(dirname "$target_file")"
  ln -s "$source_file" "$target_file"
}

link_config _home/.config/fontconfig/vicinae-fonts.conf \
  .config/fontconfig/vicinae-fonts.conf
link_config _home/.config/systemd/user/vicinae.service.d/emoji-font.conf \
  .config/systemd/user/vicinae.service.d/emoji-font.conf
```

Install the tested color emoji font from the official Google Noto Emoji
repository and verify its checksum:

```bash
font_dir="$HOME/.local/share/fonts/vicinae-emoji-cbdt"
font_file="$font_dir/NotoColorEmoji.ttf"
mkdir -p "$font_dir"
curl -fL \
  'https://github.com/googlefonts/noto-emoji/raw/refs/tags/v2.048/fonts/NotoColorEmoji.ttf' \
  -o "$font_file"
printf '%s  %s\n' \
  '3ed77810c203e1a67735dc19d395f32c23f2d7c0c3696690f4f78e15e57ab816' \
  "$font_file" | sha256sum --check -
fc-cache -f "$font_dir"
```

Reload and restart Vicinae so the service reads the drop-in:

```bash
systemctl --user daemon-reload
systemctl --user restart vicinae.service
```

Confirm Fontconfig selects the downloaded font:

```bash
FONTCONFIG_FILE="$HOME/.config/fontconfig/vicinae-fonts.conf" \
  fc-match -f '%{file}\n' 'Noto Color Emoji'
```

The result should end in
`/.local/share/fonts/vicinae-emoji-cbdt/NotoColorEmoji.ttf`.

The relevant files in this repository are:

- `_home/.config/fontconfig/vicinae-fonts.conf`
- `_home/.config/systemd/user/vicinae.service.d/emoji-font.conf`

The font file stays out of Git. The pinned upstream URL and SHA-256 above
reinstall the exact tested font after a fresh system install. Reinstalling or
updating Vicinae alone should not remove the per-user service override.
