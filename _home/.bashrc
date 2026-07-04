# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific environment
if [ -f "$HOME/.cargo/env" ]; then
    . "$HOME/.cargo/env"
fi

export ANDROID_HOME="$HOME/Android/Sdk"
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"

for p in \
    "$HOME/.local/share/fnm" \
    "$HOME/.bun/bin" \
    "$HOME/.npm-global/bin" \
    "$HOME/.local/bin" \
    "$HOME/bin" \
    "$HOME/script" \
    "$HOME/Android/Sdk/platform-tools" \
    "$HOME/Android/Sdk/emulator" \
    "$HOME/Android/Sdk/cmdline-tools/latest/bin" \
    "$HOME/Android/Sdk/tools/bin" \
    "$HOME/Android/Sdk/tools" \
    "$HOME/go/bin" \
    "/home/linuxbrew/.linuxbrew/bin" \
; do
    [ -d "$p" ] || continue
    case ":$PATH:" in
        *":$p:"*) ;;
        *) PATH="$p:$PATH" ;;
    esac
done
export PATH
unset p

# mise
if command -v mise >/dev/null 2>&1; then
    eval "$(mise activate bash)"
fi

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
    *":$PNPM_HOME:"*) ;;
    *) PATH="$PNPM_HOME:$PATH" ;;
esac
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
unset rc
