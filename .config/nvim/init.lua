if vim.g.vscode then
  -- VSCode extension
  require "vscode_config.keymaps"
  require "vscode_config.lazy"
else
  -- ordinary Neovim
  require("config.lazy")
end
