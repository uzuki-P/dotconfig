source ~/.config/fish/conf.d/abbr.fish
source ~/.config/fish/conf.d/keybind.fish
source ~/.config/fish/conf.d/paths.fish

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

# starship. https://starship.rs/
function starship_transient_rprompt_func
    starship module time
end
starship init fish | source
#enable_transience

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

# carapace. https://carapace-sh.github.io/carapace-bin/spec/bridge.html?highlight=fish#fish
carapace _carapace | source

# Generated for envman. Do not edit.
test -s ~/.config/envman/load.fish; and source ~/.config/envman/load.fish
