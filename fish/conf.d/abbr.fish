if status is-interactive
    abbr --add tm 'tmux new -As main'
    abbr --add tmc 'tmux new -As code'
    abbr --add tmi 'tmux new -As idea'

    abbr --add idea '~/apps/idea/bin/idea'
    abbr --add cb 'xclip -selection clipboard'
    abbr --add ll 'exa -lg --git --header'
    abbr --add la 'exa -lag --git --header'
    abbr --add lt 'exa -lagT -L=2 --git --header'
    abbr --add flutter-update 'flutter upgrade && flutter doctor && shorebird upgrade && shorebird doctor'

    abbr --add nm-on 'nordvpn set meshnet on'
    abbr --add nm-off 'nordvpn set meshnet off'

    abbr --add n-c 'nordvpn c id'
    abbr --add n-d 'nordvpn d'

    abbr --add n nvim
    #abbr --add nv 'NVIM_APPNAME=nvchad nvim'
    abbr --add lnv 'NVIM_APPNAME=lazy-vim nvim'

    abbr --add lg lazygit

    abbr --add android-emulator '~/sdk/android/emulator/emulator -avd Pixel_8a_API_28 -no-boot-anim -noaudio -no-snapshot'

    # git
    abbr --add gss 'git status --short'
    abbr --add gc 'git commit'
    abbr --add gco 'git checkout'
    abbr --add gaa 'git add -A'
    abbr --add gpr 'git pull --rebase'
    abbr --add gfap 'git fetch -ap'
    abbr --add gp 'git push'
    abbr --add gdiff 'git diff --color-words'
    abbr --add glog 'git log --graph --oneline --all --decorate'
    abbr --add glogo 'glog `git reflog | cut -c1-7`'
end
