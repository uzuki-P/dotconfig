require "nvchad.mappings"

-- add yours here

local map = vim.keymap.set

map("n", ";", ":", { desc = "CMD enter command mode" })
-- map("i", "jk", "<ESC>")

map({"n", "v"}, "<leader>y", "\"+y", { desc = "Copy to clipboard" })
map("n", "<C-A-S>", "<cmd>w !sudo tee %<CR>", { desc = "Nvimtree Toggle window" })

map({ "n", "i", "v" }, "<C-s>", "<cmd> w <cr>")
