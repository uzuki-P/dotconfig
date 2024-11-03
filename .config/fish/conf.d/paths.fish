# Setting up the Path
set -e fish_user_paths

## ADD to PATH ##
fish_add_path -ga ~/sdk/flutter/bin
fish_add_path -ga ~/sdk/android/tools
fish_add_path -ga ~/sdk/android/tools/bin
fish_add_path -ga ~/sdk/android/platform-tools
fish_add_path -ga ~/bin
fish_add_path -ga ~/.cargo/env
fish_add_path -ga /home/linuxbrew/.linuxbrew/bin
fish_add_path -ga ~/.config/composer/vendor/bin
fish_add_path -ga ~/.local/bin
fish_add_path -ga ~/.pub-cache/bin
fish_add_path -ga ~/.shorebird/bin

set -gx MANPATH /usr/local/man
set -gx ANDROID_HOME $HOME/sdk/android

# rustup shell setup
if not contains "$HOME/.cargo/bin" $PATH
    # Prepending path in case a system-installed rustc needs to be overridden
    set -x PATH "$HOME/.cargo/bin" $PATH
end
