require "nvchad.options"

-- add yours here!

local o = vim.o
o.relativenumber = true
o.clipboard = "" -- turn off clipboard. Use `<leader>y` to copy to clipboard

vim.highlight.on_yank = {higroup='Visual', timeout=300}
