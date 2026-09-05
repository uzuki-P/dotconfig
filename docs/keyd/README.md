# Caps navigation

`caps-nav.conf` targets the laptop's AT keyboard and the FEKER IK75's
currently connected 2.4 GHz receiver. It uses full keyd device fingerprints
because Solaar's virtual keyboard shares the laptop's vendor/product ID.
There is no wildcard match. Iteung is absent and its identity has not been
measured; it will remain unaffected unless it presents an identical full
fingerprint to one of the selected devices.

| Keys | Output |
| --- | --- |
| Tap Caps Lock | Escape |
| Escape | Caps Lock |
| Hold Caps + H/J/K/L | Left/Down/Up/Right |
| Hold Caps + Y/O | Home/End |
| Hold Caps + U/D | Page Up/Page Down |
| Hold Caps + other keys | Ctrl + that key, such as Ctrl + F |

The navigation layer activates immediately. Releasing Caps after navigation
does not send Escape. The layer's `:C` suffix supplies Ctrl for keys without
an explicit navigation binding. Caps + D still sends plain Page Down.
Keys pressed without Caps retain their normal bindings.

This configuration requires keyd. Follow the
[upstream installation instructions](https://github.com/rvaiya/keyd#installation),
using a stable release. It was validated with v2.6.0.

Install this file as `/etc/keyd/caps-nav.conf` and enable the system keyd
service. Stow does not install this system configuration. Administrator
access is required to install keyd, write `/etc/keyd`, and enable the service.

After activation, test Caps tap and every navigation binding on both keyboards.
Check that ordinary H/J/K/L still type letters. When Iteung is connected,
verify that its Caps and letter keys retain their original behavior.
The FEKER's wired or Bluetooth modes may have different fingerprints and
are not included in this configuration.

Use `keyd check` to validate the installed configuration and `keyd monitor`
to inspect device fingerprints. The emergency Backspace + Escape + Enter
chord terminates keyd.

For games, run `sudo systemctl stop keyd` to restore the physical keyboards'
original behavior, including Caps Lock and Escape. Run
`sudo systemctl start keyd` to restore the remapping afterward. These commands
need administrator access because keyd is a system service. Stopping it does
not change its enabled state, so an enabled service starts again at reboot.
