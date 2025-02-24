local set = vim.opt_local
set.shiftwidth = 2
set.tabstop = 2

set.foldmethod = "manual"
set.foldlevelstart = 4

set.commentstring = "// %s"

vim.lsp.inlay_hint.enable(false)
