# Setting up the Path
set -e fish_user_paths

## ADD to PATH ##
#fish_add_path -ga ~/sdk/flutter/bin
fish_add_path -ga ~/sdk/android/tools
fish_add_path -ga ~/go/bin
fish_add_path -ga ~/sdk/android/tools/bin
fish_add_path -ga ~/sdk/android/platform-tools
fish_add_path -ga ~/script
fish_add_path -ga ~/bin
fish_add_path -ga ~/.cargo/env
fish_add_path -ga /home/linuxbrew/.linuxbrew/bin
fish_add_path -ga ~/.config/composer/vendor/bin
fish_add_path -ga ~/.local/bin
fish_add_path -ga ~/.pub-cache/bin
fish_add_path -ga ~/.shorebird/bin
fish_add_path -ga ~/.puro/bin
fish_add_path -ga ~/.puro/shared/pub_cache/bin
fish_add_path -ga ~/.puro/envs/default/flutter/bin
fish_add_path -ga ~/.npm-global/bin

## for bootdev https://github.com/bootdotdev/bootdev?tab=readme-ov-file#1-install-go-122-or-later
fish_add_path -ga ~/.local/opt/go/bin

set -gx MANPATH /usr/local/man
set -gx JAVA_HOME /usr/lib/jvm/java-17-openjdk-17.0.14.0.7-1.fc41.x86_64
set -gx ANDROID_HOME $HOME/sdk/android
set -gx ANDROID_SDK $HOME/sdk/android
set -gx PURO_ROOT $HOME/.puro
set -gx PUB_CACHE $HOME/.puro/shared/pub_cache

# rustup shell setup
if not contains "$HOME/.cargo/bin" $PATH
    # Prepending path in case a system-installed rustc needs to be overridden
    set -x PATH "$HOME/.cargo/bin" $PATH
end
