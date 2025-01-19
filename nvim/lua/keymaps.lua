-- [[ Basic Keymaps ]]
--  See `:help vim.keymap.set()`

-- Clear highlights on search when pressing <Esc> in normal mode
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>')

-- Diagnostic keymaps
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostic [Q]uickfix list' })

-- Exit terminal mode in the builtin terminal with a shortcut that is a bit easier
-- for people to discover. Otherwise, you normally need to press <C-\><C-n>, which
-- is not what someone will guess without a bit more experience.
--
-- NOTE: This won't work in all terminal emulators/tmux/etc. Try your own mapping
-- or just use <C-\><C-n> to exit terminal mode
vim.keymap.set('t', '<Esc><Esc>', '<C-\\><C-n>', { desc = 'Exit terminal mode' })

-- Keybinds to make split navigation easier.
--  Use CTRL+<hjkl> to switch between windows
--
--  See `:help wincmd` for a list of all window commands
vim.keymap.set('n', '<C-h>', '<C-w><C-h>', { desc = 'Move focus to the left window' })
vim.keymap.set('n', '<C-l>', '<C-w><C-l>', { desc = 'Move focus to the right window' })
vim.keymap.set('n', '<C-j>', '<C-w><C-j>', { desc = 'Move focus to the lower window' })
vim.keymap.set('n', '<C-k>', '<C-w><C-k>', { desc = 'Move focus to the upper window' })

-- [[ Basic Autocommands ]]
--  See `:help lua-guide-autocommands`

-- Highlight when yanking (copying) text
--  Try it with `yap` in normal mode
--  See `:help vim.highlight.on_yank()`
vim.api.nvim_create_autocmd('TextYankPost', {
  desc = 'Highlight when yanking (copying) text',
  group = vim.api.nvim_create_augroup('kickstart-highlight-yank', { clear = true }),
  callback = function()
    vim.highlight.on_yank()
  end,
})

vim.keymap.set({ 'n', 'v' }, '<leader>y', '"+y', { desc = 'Copy to clipboard' })
-- vim.keymap.set({ 'n', 'v' }, '<leader>p', '"+p', { desc = 'Paste from clipboard' })

-- better indent handling
vim.keymap.set('v', '<', '<gv', { desc = 'Remove Indent' })
vim.keymap.set('v', '>', '>gv', { desc = 'Add Indent' })

-- vim.keymap.set('v', 'J', ':m .+1<CR>==', { desc = 'Move whole line down' })
-- vim.keymap.set('v', 'K', ':m .-2<CR>==', { desc = 'Move whole line up' })
-- vim.keymap.set('x', 'J', ":move '>+1<CR>gv-gv", { desc = 'Move whole line down' })
-- vim.keymap.set('x', 'K', ":move '<-2<CR>gv-gv", { desc = 'Move whole line up' })

vim.keymap.set('v', 'p', '"_dP', { desc = 'Paste preserves primal yanked piece' })

vim.keymap.set('n', '<M-p>', '<cmd>cprev<CR>', { desc = 'Jump to prev error' })
vim.keymap.set('n', '<M-n>', '<cmd>cnext<CR>', { desc = 'Jump to next error' })

vim.keymap.set('n', '<space>nr', '<cmd>source $MYVIMRC | echo "config reloaded"<CR>', { desc = '[N]vim [R]eload' })

-- vim.keymap.set('n', '-', '<CMD>Oil<CR>', { desc = 'Open parent directory' })

vim.keymap.set('n', '<space>x', '<cmd>bd<CR>', { desc = '[B]uffer [C]lose' })

vim.keymap.set('n', '<space>b_', '<cmd>vs<CR>', { desc = '[B]uffer Split |' })
vim.keymap.set('n', '<space>b-', '<cmd>split<CR>', { desc = '[B]uffer Split --' })

-- vim.keymap.set('n', '<space>l', ':.lua<CR>')
-- vim.keymap.set('v', '<space>l', ':lua<CR>')

-- unmap 's' single char replacement for easier nvim.surround
vim.keymap.set('n', 's', '', {})

-- Map Ctrl + S to save the current file in normal mode
vim.keymap.set('n', '<C-s>', ':w<CR>', { desc = 'Save file' })

vim.keymap.set('n', '<Tab>', ':bnext<CR>', { desc = 'Next tab/buffer' })
vim.keymap.set('n', '<S-Tab>', ':bprev<CR>', { desc = 'Next tab/buffer' })

-- vim: ts=2 sts=2 sw=2 et
