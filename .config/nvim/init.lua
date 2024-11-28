if vim.g.vscode then
  -- VSCode extension
  require "user.vscode_keymaps"

  require("config.lazy")
else
  -- ordinary Neovim
  require("config.lazy")
end
