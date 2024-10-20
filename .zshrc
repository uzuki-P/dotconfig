# Add deno completions to search path
if [[ ":$FPATH:" != *":/home/uzuki_p/.zsh/completions:"* ]]; then export FPATH="/home/uzuki_p/.zsh/completions:$FPATH"; fi
export ZSH="$HOME/.oh-my-zsh"

# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="amuse-custom"

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Auto-update behavior
zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
#COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

plugins=(
  git-prompt
  ssh-agent
  zsh-autosuggestions
  zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# User configuration

export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

#export JAVA_HOME=/home/uzuki_p/.jdks/azul-17.0.11
export ANDROID_HOME=$HOME/sdk/android

# Set JAVA_HOME using asdf-vm
#. $HOME/.asdf/plugins/java/set-java-home.zsh
# set GOROOT
#. "$HOME/.asdf/plugins/golang/set-env.zsh"

# Set cargo from rustup
. "$HOME/.cargo/env"

# Path
export PATH=$PATH:$HOME/sdk/flutter/bin
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools
export PATH=$PATH:$HOME/bin
export PATH=$PATH:$HOME/.cargo/env
export PATH=$PATH:/home/linuxbrew/.linuxbrew/bin
export PATH=$PATH:$HOME/.config/composer/vendor/bin
export PATH=$PATH:$HOME/.local/bin

export PATH=$PATH:$HOME/bin/clipboard-linux-amd64/bin

# directory colors
eval `dircolors ~/dircolors.256dark`

export VISUAL=vim
export EDITOR="$VISUAL"

# sudosu for zsh
alias sudosu='sudo -E -s'

# sort dot file first when ll
alias la='LC_COLLATE=C ls -AhlF'
alias ll='LC_COLLATE=C ls -lh'

# aliases for agnoster theme
export DEFAULT_USER="$(whoami)"
prompt_context () { }

# force tmux using true color
#alias tmux='TERM=screen-256color tmux -2'
alias tm='tmux new -As main'

# git convenience
alias gss='git status --short'
alias gc='git commit'
alias gaa='git add -A'
alias gpr='git pull --rebase'
alias gfap='git fetch -ap'
alias gp='git push'
alias gdiff='git diff --color-words'
alias glog='git log --graph --oneline --all --decorate'
alias glogo='glog `git reflog | cut -c1-7`'

# ranger. Move to working directory when close.
alias ranger='ranger --choosedir=$HOME/.rangerdir; LASTDIR=`cat $HOME/.rangerdir`; cd "$LASTDIR"'

# intellij
alias idea='/home/uzuki_p/apps/idea/bin/idea'

# copy to clipboard
alias cb='xclip -selection clipboard'

# set cd as zoxide
eval "$(zoxide init --cmd cd zsh)"

# nvim
alias nv='NVIM_APPNAME="nvchad" nvim'

## [Completion]
## Completion scripts setup. Remove the following line to uninstall
[[ -f /home/uzuki_p/.dart-cli-completion/zsh-config.zsh ]] && . /home/uzuki_p/.dart-cli-completion/zsh-config.zsh || true
## [/Completion]

# Shorebird config
export PATH="/home/uzuki_p/.shorebird/bin:$PATH"

# flutter pub global package
export PATH="$PATH":"$HOME/.pub-cache/bin"

. "/home/uzuki_p/.deno/env"
# Initialize zsh completions (added by deno install script)
autoload -Uz compinit
compinit

