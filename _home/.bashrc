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
alias tm='tmux new -As main'
alias cb='xclip -selection clipboard'
alias ll='eza -lg --git --header'
alias la='eza -lag --git --header'
alias lt='eza -lagT -L=2 --git --header'

alias nm-on='nordvpn set meshnet on'
alias nm-off='nordvpn set meshnet off'
alias n-d='nordvpn d'

alias n='nvim'
alias lg='lazygit'
alias ccd='claude --dangerously-skip-permissions'
alias ubuntu-db='distrobox enter ubuntu -- fish'

# herdr new tab
alias hnt='herdr tab create --cwd "$PWD" --focus && herdr'

# git
alias gss='git status --short'
alias gc='git commit'
alias gco='git checkout'
alias gaa='git add -A'
alias gpr='git pull --rebase'
alias gpnr='git pull --no-rebase'
alias gfap='git fetch -ap'
alias gp='git push'
alias gdiff='git diff --color-words'
alias glog='git log --graph --oneline --all --decorate'
alias glogo='glog `git reflog | cut -c1-7`'

if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
unset rc

# Vite+ bin (https://viteplus.dev)
. "$HOME/.vite-plus/env"

# Added by codebase-memory-mcp install
export PATH="/home/uzuki_p/.local/bin:$PATH"

# opencode
export PATH=/home/uzuki_p/.opencode/bin:$PATH
