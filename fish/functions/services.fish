# Inventory and control of everything that runs on this machine, so there is
# one command to see what exists, whether it starts at boot, where it lives,
# and to start/stop/boot-toggle it without remembering the mechanism.
# Edit this file to change the inventory; it auto-loads in fish.
#
#   services                        inventory
#   services start|stop|restart|status <name>
#   services on|off <name>          boot only
function services --description "Inventory and control of my services"
    set -l quad_dir ~/.config/containers/systemd
    set -l unit_dir ~/.config/systemd/user

    if test (count $argv) -eq 0
        _services_inventory $quad_dir $unit_dir
        return 0
    end

    set -l verb $argv[1]
    set -l name $argv[2]
    if test (count $argv) -ne 2; or not contains -- $verb start stop restart status on off
        echo "usage: services                          inventory" >&2
        echo "       services start|stop|restart|status <name>" >&2
        echo "       services on|off <name>            start-at-boot" >&2
        return 2
    end

    set -l kind (_services_kind $quad_dir $unit_dir $name)
    if test -z "$kind"
        echo "services: no service named '$name'" >&2
        return 1
    end

    set -l unit $name.service
    switch $kind
        case quadlet
            switch $verb
                case start
                    if test -e $quad_dir/$name.container.disabled
                        echo "services: $name boot is off (use: services on $name)" >&2
                        return 1
                    end
                    systemctl --user start $unit
                case stop
                    systemctl --user stop $unit
                case restart
                    systemctl --user restart $unit
                case status
                    if test -e $quad_dir/$name.container.disabled
                        echo "services: $name boot is off (use: services on $name)" >&2
                        return 1
                    end
                    systemctl --user status --no-pager $unit
                case on
                    if test -e $quad_dir/$name.container.disabled
                        mv $quad_dir/$name.container.disabled $quad_dir/$name.container
                        systemctl --user daemon-reload
                    end
                    echo "$name: boot on"
                case off
                    if test -e $quad_dir/$name.container
                        systemctl --user stop $unit 2>/dev/null
                        mv $quad_dir/$name.container $quad_dir/$name.container.disabled
                        systemctl --user daemon-reload
                    end
                    echo "$name: boot off"
            end
        case unit
            switch $verb
                case start
                    systemctl --user start $unit
                case stop
                    systemctl --user stop $unit
                case restart
                    systemctl --user restart $unit
                case status
                    systemctl --user status --no-pager $unit
                case on
                    systemctl --user enable $unit
                case off
                    systemctl --user disable --now $unit
            end
        case compose
            set -l dir (_services_compose_dir $name)
            switch $verb
                case start
                    podman compose --project-directory $dir up -d
                case stop
                    podman compose --project-directory $dir stop
                case restart
                    podman compose --project-directory $dir restart
                case status
                    podman compose --project-directory $dir ps
                case on off
                    echo "services: $name boots via the 'restart:' policy in $dir/compose.yaml" >&2
                    return 1
            end
    end
end

function _services_inventory --argument-names quad_dir unit_dir
    set_color --bold
    echo "quadlets  ($quad_dir)"
    set_color normal
    for f in $quad_dir/*.container $quad_dir/*.container.disabled
        test -e $f; or continue
        set -l file (path basename $f)
        set -l name (string replace -r '\.container(\.disabled)?$' '' -- $file)
        set -l boot on
        set -l run down
        string match -q '*.disabled' -- $file; and set boot off
        systemctl --user is-active --quiet $name.service 2>/dev/null; and set run up
        set -l desc (grep -m1 '^Description=' $f | string replace -r '^Description=' '')
        printf '  %-22s boot %-3s %-4s %s\n' $name $boot $run "$desc"
        printf '  %-22s %s\n' '' (string replace --regex "^$HOME" '~' -- (path resolve $f))
    end

    set_color --bold
    echo "user units ($unit_dir)"
    set_color normal
    for f in $unit_dir/*.service $unit_dir/*.timer
        test -e $f; or continue
        set -l unit (path basename $f)
        set -l name (string replace -r '\.(service|timer)$' '' -- $unit)
        set -l boot (systemctl --user is-enabled $unit 2>/dev/null)
        test -z "$boot"; and set boot off
        set -l run down
        systemctl --user is-active --quiet $unit 2>/dev/null; and set run up
        set -l desc (grep -m1 '^Description=' $f | string replace -r '^Description=' '')
        printf '  %-22s boot %-3s %-4s %s\n' $name $boot $run "$desc"
        printf '  %-22s %s\n' '' (string replace --regex "^$HOME" '~' -- (path resolve $f))
    end

    set_color --bold
    echo "compose stacks  (~/projects)"
    set_color normal
    for f in ~/projects/*/compose.yaml ~/projects/_sandbox/*/compose.yaml
        test -e $f; or continue
        set -l dir (path dirname $f)
        set -l name (path basename $dir)
        set -l boot off
        grep -q 'restart: always' $f; and set boot on
        set -l n (grep -cE '^  [a-zA-Z0-9_-]+:' $f)
        printf '  %-22s boot %-3s %-4s %s\n' $name $boot up "$n services"
        printf '  %-22s %s\n' '' (string replace --regex "^$HOME" '~' -- $dir)
    end

    echo
    echo "on/off = start at boot. start/stop/restart/status = now. names resolve across quadlets, user units, and compose stacks"
end

function _services_kind --argument-names quad_dir unit_dir name
    test -e $quad_dir/$name.container; and echo quadlet; and return 0
    test -e $quad_dir/$name.container.disabled; and echo quadlet; and return 0
    test -e $unit_dir/$name.service; and echo unit; and return 0
    test -e $unit_dir/$name.timer; and echo unit; and return 0
    test -e ~/projects/$name/compose.yaml; and echo compose; and return 0
    test -e ~/projects/_sandbox/$name/compose.yaml; and echo compose; and return 0
    return 1
end

function _services_compose_dir --argument-names name
    test -e ~/projects/$name/compose.yaml; and echo ~/projects/$name; and return 0
    echo ~/projects/_sandbox/$name
end
