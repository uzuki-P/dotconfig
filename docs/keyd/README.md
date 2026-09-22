# Caps navigation

`caps-nav.conf` targets the laptop's AT keyboard, the FEKER IK75's
currently connected 2.4 GHz receiver, and Sunshine's "Keyboard passthrough"
virtual keyboard, which carries input from Moonlight clients. It uses full
keyd device fingerprints because Solaar's virtual keyboard shares the
laptop's vendor/product ID, and Sunshine's virtual devices all share the
vendor/product ID `beef:dead`, so matching on it alone would also select
Sunshine's mouse, touch, and pen devices. There is no wildcard match.
Iteung is absent and its identity has not been measured; when connected
directly it remains unaffected unless it presents an identical full
fingerprint to one of the selected devices. Input streamed from a Moonlight
client, including Iteung, does travel through the Sunshine virtual keyboard
and is remapped.

| Keys | Output |
| --- | --- |
| Tap Caps Lock | Escape |
| Escape | Caps Lock |
| Hold Caps + H/J/K/L | Left/Down/Up/Right |
| Hold Caps + Y/O | Home/End |
| Hold Caps + U/I | Page Down/Page Up |
| Hold Caps + other keys | Ctrl + that key, such as Ctrl + F |

The navigation layer activates immediately. Releasing Caps after navigation
does not send Escape. The layer's `:C` suffix supplies Ctrl for keys without
an explicit navigation binding. D has no navigation binding, so Caps + D
sends Ctrl + D.
Keys pressed without Caps retain their normal bindings.

This configuration requires keyd. Follow the
[upstream installation instructions](https://github.com/rvaiya/keyd#installation),
using a stable release. It was validated with v2.6.0.

Install this file as `/etc/keyd/caps-nav.conf` and enable the system keyd
service. Stow does not install this system configuration. Administrator
access is required to install keyd, write `/etc/keyd`, and enable the service.

After activation, test Caps tap and every navigation binding on both keyboards,
and once during a Moonlight stream to confirm the streamed input is remapped.
Check that ordinary H/J/K/L still type letters. When Iteung is connected,
verify that its Caps and letter keys retain their original behavior.
The FEKER's wired or Bluetooth modes may have different fingerprints and
are not included in this configuration.

Sunshine creates its virtual devices with fixed names, so the fingerprint
should survive reboots. If a Sunshine update changes it, keyd silently stops
matching that device; re-measure with `sudo keyd monitor` while the devices
exist and update the `[ids]` entry.

Use `keyd check` to validate the installed configuration and `keyd monitor`
to inspect device fingerprints. The emergency Backspace + Escape + Enter
chord terminates keyd.

For games, run `sudo systemctl stop keyd` to restore the physical keyboards'
original behavior, including Caps Lock and Escape. Run
`sudo systemctl start keyd` to restore the remapping afterward. These commands
need administrator access because keyd is a system service. Stopping it does
not change its enabled state, so an enabled service starts again at reboot.
