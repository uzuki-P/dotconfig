require "nvchad.mappings"

-- add yours here

local map = vim.keymap.set

map("n", ";", ":", { desc = "CMD enter command mode" })
map("n", "<A-1>", "<cmd>NvimTreeToggle<CR>", { desc = "Nvimtree Toggle window" })
map({"n", "v"}, "<leader>y", "\"+y", { desc = "Copy to clipboard" })

-- map("i", "jk", "<ESC>")
-- map({ "n", "i", "v" }, "<C-s>", "<cmd> w <cr>")
