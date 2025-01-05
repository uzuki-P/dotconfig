set number	        " Show line numbers
set linebreak	      " Break lines at word (requires Wrap lines)
set showbreak=+++   " Wrap-broken line prefix
set textwidth=100   " Line wrap (number of cols)
set showmatch	      " Highlight matching brace
 
set hlsearch	      " Highlight all search results
set smartcase	      " Enable smart-case search
set ignorecase	    " Always case-insensitive
set incsearch	      " Searches for strings incrementally
 
set autoindent	    " Auto-indent new lines
set shiftwidth=4    " Number of auto-indent spaces
set smartindent	    " Enable smart-indent
set smarttab	      " Enable smart-tabs
set softtabstop=4   " Number of spaces per Tab
 
set ruler	 
set relativenumber
set backspace=indent,eol,start	" Backspace behaviour

syntax enable
set background=dark
hi Normal guibg=NONE ctermbg=NONE

" Cursor in terminal
" https://vim.fandom.com/wiki/Configuring_the_cursor
" 1 or 0 -> blinking block
" 2 solid block
" 3 -> blinking underscore
" 4 solid underscore
" Recent versions of xterm (282 or above) also support
" 5 -> blinking vertical bar
" 6 -> solid vertical bar
if &term =~ '^xterm'
  " normal mode
  let &t_EI .= "\<Esc>[0 q"
  " insert mode
  let &t_SI .= "\<Esc>[6 q"
endif
