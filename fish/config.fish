source ~/.config/fish/conf.d/abbr.fish
source ~/.config/fish/conf.d/paths.fish
source ~/.config/fish/conf.d/rustup.fish

function fish_greeting
    switch (random 1 5)
        case 1
            echo "🐟"
        case 2
            echo "🐠"
        case 3
            echo "🐡"
        case 4
            echo "🐋"
        case 5
            echo "🦈"
    end
end

# A fresh tmux client queries ttyd/xterm.js for terminal capabilities. On the
# last-session-to-new-server transition, its late Device Attributes reply can
# reach fish as keyboard input. Consume that reply and repaint the prompt.
function fish_user_key_bindings
    set -l ttyd_device_attributes (string unescape '\e[?61;4;6;7;14;21;22;23;24;28;32;42;52c')
    bind $ttyd_device_attributes repaint
end
fish_user_key_bindings

# starship. https://starship.rs/
function starship_transient_rprompt_func
    starship module time
end
starship init fish | source
#enable_transience

# mise https://mise.en.dev/
mise activate fish | source

# zoxide. https://github.com/ajeetdsouza/zoxide
zoxide init --cmd cd fish | source

# yazi. https://yazi-rs.github.io/docs/quick-start#shell-wrapper
function y
    set tmp (mktemp -t "yazi-cwd.XXXXXX")
    yazi $argv --cwd-file="$tmp"
    if set cwd (command cat -- "$tmp"); and [ -n "$cwd" ]; and [ "$cwd" != "$PWD" ]
        builtin cd -- "$cwd"
    end
    rm -f -- "$tmp"
end

# pnpm.
set -gx PNPM_HOME "/home/uzuki_p/.local/share/pnpm"
if not string match -q -- $PNPM_HOME $PATH
    set -gx PATH "$PNPM_HOME" $PATH
end

# fnm
#fnm env --use-on-cd --shell fish | source

# carapace. https://github.com/carapace-sh/carapace-bin/releases
carapace _carapace | source

# Generated for envman. Do not edit.
#test -s ~/.config/envman/load.fish; and source ~/.config/envman/load.fish
