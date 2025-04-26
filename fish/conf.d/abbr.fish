if status is-interactive
    abbr --add tm 'tmux new -As main'
    abbr --add tmc 'tmux new -As code'
    abbr --add tmi 'tmux new -As idea'

    abbr --add idea '~/apps/idea/bin/idea'
    abbr --add cb 'xclip -selection clipboard'
    abbr --add ll 'eza -lg --git --header'
    abbr --add la 'eza -lag --git --header'
    abbr --add lt 'eza -lagT -L=2 --git --header'

    abbr --add nm-on 'nordvpn set meshnet on'
    abbr --add nm-off 'nordvpn set meshnet off'

    abbr --add n-c 'nordvpn c id'
    abbr --add n-d 'nordvpn d'

    abbr --add n nvim
    abbr --add nv 'NVIM_APPNAME=nvim-bak nvim'

    abbr --add lg lazygit

    abbr --add android-emulator '~/sdk/android/emulator/emulator -avd Pixel_8a_API_28 -no-boot-anim -noaudio -no-snapshot'

    # git
    abbr --add gss 'git status --short'
    abbr --add gc 'git commit'
    abbr --add gco 'git checkout'
    abbr --add gaa 'git add -A'
    abbr --add gpr 'git pull --rebase'
    abbr --add gpnr 'git pull --no-rebase'
    abbr --add gfap 'git fetch -ap'
    abbr --add gp 'git push'
    abbr --add gdiff 'git diff --color-words'
    abbr --add glog 'git log --graph --oneline --all --decorate'
    abbr --add glogo 'glog `git reflog | cut -c1-7`'
end
