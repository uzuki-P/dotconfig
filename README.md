# Setup

```
git clone https://github.com/uzuki-P/dotconfig ~/dotconfig
```

# Install Dependencies

## Required: 

```
stow neovim vim zsh tmux zoxide gcc make git ripgrep fd-find unzip 
```

## Optional: 

```
ranger btop composer composer dust atuin 
```

# Install [oh-my-zsh](https://ohmyz.sh/#install)

```
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

## Optional:

Autocompletion & syntax highlight

```
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

# Install [oh-my-tmux](https://github.com/gpakosz/.tmux?tab=readme-ov-file#installation)

```
cd
git clone https://github.com/gpakosz/.tmux.git
ln -s -f .tmux/.tmux.conf
```

# Install [asdf](https://asdf-vm.com/guide/getting-started.html#official-download)

```
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
```

# Install [homebrew](https://brew.sh/)

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

# Install rust with [rustup](https://rustup.rs/)

```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

# Install [android studio](https://developer.android.com/studio)

Extract android studio to `~/apps/android-studio` folder. Set the `android-sdk` folder to `~/sdk/android`.

> Use `tar xvf` to extract.

# Install  [Flutter](https://docs.flutter.dev/get-started/install/linux/android?tab=download#install-the-flutter-sdk)

Extract to `~/sdk/flutter`.

> Use `tar xvf` to extract.

# Run stow on this directory

```
cd ~/dotconfig
stow . --adopt
git reset --hard
```

# Setup [asdf plugin](https://asdf-vm.com/manage/plugins.html#add)

```
asdf plugin add java
asdf plugin add gleam 
asdf plugin add erlang 
asdf plugin add nodejs 
```

## Install plugin

```
cd 
asdf install
```

