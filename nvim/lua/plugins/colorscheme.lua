return {
  { "catppuccin/nvim" },
  { "yorik1984/newpaper.nvim" },
  { "sainnhe/edge" },
  { "morhetz/gruvbox" },
  { "chiendo97/intellij.vim" },
  {
    "f-person/auto-dark-mode.nvim",
    -- enabled = false,
    lazy = false,
    priority = 1000,
    opts = {
      fallback = "light",
      update_interval = 1000,
      set_dark_mode = function()
        vim.api.nvim_set_option_value("background", "dark", {})
        vim.cmd.colorscheme("tokyonight")
      end,
      set_light_mode = function()
        vim.api.nvim_set_option_value("background", "light", {})
        vim.cmd.colorscheme("catppuccin-latte")
      end,
    },
  },
}
