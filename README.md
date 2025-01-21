> NOTE:
> [oh-my-tmux](https://github.com/gpakosz/.tmux) is already on `.config/tmux`  
> I personally use fish (and trying nushell)

# Setup

```bash
git clone https://github.com/uzuki-P/dotconfig ~/dotconfig
```

## Install Dependencies

```
fish stow neovim tmux zoxide
gcc make git ripgrep fd-find unzip 
```

## Install rust with [rustup](https://rustup.rs/)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Install [puro](https://puro.dev/) (flutter version manager)

```bash
puro create stable stable
puro use -g stable
```

## Install [intellij idea ce](https://www.jetbrains.com/idea/download)

On download page scroll a bit to download the community edition. Download flutter and android plugins. Restart IDE. Create android project and set `android-sdk` folder to `~/sdk/android`.

> Use `tar xvf` to extract.

## Run setup.sh

There's might be some conflict since config files might be created when we install the dependencies. So we need to call `--adopt` manually first. 

```
cd ~/dotconfig
stow . --adopt
git reset --hard    # change the default config to dotconfig
./setup.sh          # stow the config & _home folder
```

# NOTES

## change java version on fedora

```bash
sudo alternatives --config java
```

## zsh config:

Autocompletion & syntax highlight for zsh:

```bash
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

