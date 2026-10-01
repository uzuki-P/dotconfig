# Send files with KDE Connect

`_home/script/kde-send` is a Bash executable you can call from fish or bash.
The repository's home Stow target exposes it as `~/script/kde-send`.
Fish already adds `~/script` to PATH. From Bash, use that full path or add the
directory to PATH.

Both `-l` and `--list` list available device IDs and names.

```sh
~/script/kde-send --list
~/script/kde-send "My Phone" ./report.pdf ./photo.jpg
~/script/kde-send --dry-run "My Phone" ./report.pdf
~/script/kde-send --device-id DEVICE_ID ./report.pdf
```

Names match exactly and include case. Duplicate available names require an
explicit device ID. The script checks every file before requesting a transfer
and stops at the first failed request. Directories need to be archived first.
Quote paths with spaces. Shell globs such as `./photos/*.jpg` work in both shells.

KDE Connect must be installed, and the destination must be paired and reachable.
Run from your desktop user session with access to its D-Bus. If a terminal outside
that session reports `Not connected to D-Bus server`, use a desktop terminal or
configure that terminal to access the existing user session bus.

`--dry-run` resolves the device and prints Bash-escaped commands without sending.
Exit status 0 means KDE Connect accepted the share requests. It does not confirm
that the destination received the files. Exit status 1 means file validation,
device selection, or a CLI request failed. Exit status 2 means invalid usage.

## Using it from a skill

A future skill can call `~/script/kde-send` directly. Resolve the user's files and
destination, use `--list` when device discovery is needed, then pass each path as
a separate argument. Keep device names and IDs out of the skill unless the user
requests a saved default. Do not pick the first device or retry partial batches
automatically. Report submitted requests separately from confirmed delivery.

The underlying CLI also supports a direct single-file command:

```sh
kdeconnect-cli --name "My Phone" --share ./report.pdf
```

See the [KDE CLI source](https://invent.kde.org/network/kdeconnect-kde/-/blob/master/cli/kdeconnect-cli.cpp)
for name selection and share request behavior.
