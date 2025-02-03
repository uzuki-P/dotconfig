-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here

vim.g.snacks_animate = false

local opt = vim.opt

opt.shell = "fish"

opt.wrap = false
opt.linebreak = true
opt.showbreak = "↪ "
opt.textwidth = 120
opt.wrapmargin = 5

opt.number = true
opt.relativenumber = true

opt.shiftwidth = 2
opt.tabstop = 2

opt.ruler = true
opt.colorcolumn = "80,120"

opt.foldmethod = "syntax"

-- Enable mouse mode, can be useful for resizing splits for example!
opt.mouse = "a"

-- Don't show the mode, since it's already in the status line
opt.showmode = false

-- Use `<leader>y` to copy to clipboard
--  See `:help 'clipboard'`
-- vim.schedule(function()
opt.clipboard = ""
-- end)

-- Enable break indent
opt.breakindent = true

-- Save undo history
opt.undofile = true

-- Case-insensitive searching UNLESS \C or one or more capital letters in the search term
opt.ignorecase = true
opt.smartcase = true
opt.incsearch = true

-- Keep signcolumn on by default
opt.signcolumn = "yes"

-- Decrease update time
opt.updatetime = 250

-- Decrease mapped sequence wait time
opt.timeoutlen = 300

-- Configure how new splits should be opened
opt.splitright = true
opt.splitbelow = true

-- Sets how neovim will display certain whitespace characters in the editor.
--  See `:help 'list'`
--  and `:help 'listchars'`
opt.list = true
opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }

-- Preview substitutions live, as you type!
opt.inccommand = "split"

-- Show which line your cursor is on
opt.cursorline = true

-- Minimal number of screen lines to keep above and below the cursor.
opt.scrolloff = 10

-- for obsidian.vim
opt.conceallevel = 1
