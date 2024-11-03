# Custom sourcing of colors, exports, paths, grc, multi-function fish files, etc.
source ~/.config/fish/conf.d/abbr.fish
source ~/.config/fish/conf.d/colors.fish # this could be obsolete by starship & eza
source ~/.config/fish/conf.d/paths.fish

function starship_transient_rprompt_func
  starship module time
end
starship init fish  | source
enable_transience

# zoxide
zoxide init --cmd cd fish  | source

# setup yazi. https://yazi-rs.github.io/docs/quick-start#shell-wrapper
function y
	set tmp (mktemp -t "yazi-cwd.XXXXXX")
	yazi $argv --cwd-file="$tmp"
	if set cwd (command cat -- "$tmp"); and [ -n "$cwd" ]; and [ "$cwd" != "$PWD" ]
		builtin cd -- "$cwd"
	end
	rm -f -- "$tmp"
end
