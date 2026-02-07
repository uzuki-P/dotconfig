# Setting up the Path
set -e fish_user_paths

## ADD to PATH ##
#fish_add_path -ga ~/sdk/flutter/bin
fish_add_path -ga /home/linuxbrew/.linuxbrew/bin
fish_add_path -ga ~/sdk/android/tools
fish_add_path -ga ~/go/bin
fish_add_path -ga ~/sdk/android/tools/bin
fish_add_path -ga ~/sdk/android/platform-tools
fish_add_path -ga ~/script
fish_add_path -ga ~/bin
fish_add_path -ga ~/.config/composer/vendor/bin
fish_add_path -ga ~/.local/bin
fish_add_path -ga ~/.pub-cache/bin
fish_add_path -ga ~/.shorebird/bin
fish_add_path -ga ~/.puro/bin
fish_add_path -ga ~/.puro/shared/pub_cache/bin
fish_add_path -ga ~/.puro/envs/default/flutter/bin
fish_add_path -ga ~/.npm-global/bin
fish_add_path -ga ~/.maestro/bin
fish_add_path -ga ~/apps/scrcpy # make sure below android/tools 
fish_add_path -ga ~/.opencode/bin
fish_add_path -ga ~/.bun/bin

## for bootdev https://github.com/bootdotdev/bootdev?tab=readme-ov-file#1-install-go-122-or-later
fish_add_path -ga ~/.local/opt/go/bin

set -gx VISUAL nvim
set -gx EDITOR nvim
set -gx MANPATH /usr/local/man
set -gx JAVA_HOME /usr/lib/jvm/temurin-17-jdk
set -gx ANDROID_HOME $HOME/sdk/android
set -gx ANDROID_SDK $HOME/sdk/android
set -gx PURO_ROOT $HOME/.puro
set -gx PUB_CACHE $HOME/.puro/shared/pub_cache
set -gx BUN_INSTALL $HOME/.bun

set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/ssh-agent.socket"

# copyq wayland. https://github.com/hluk/CopyQ/issues/27#issuecomment-549766568
set -gx QT_QPA_PLATFORM xcb
