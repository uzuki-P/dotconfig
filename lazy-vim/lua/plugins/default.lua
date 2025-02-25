return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    enabled = false,
  },
  {
    "folke/snacks.nvim",
    opts = {
      dashboard = {
        enabled = true,
      },
    },
  },
  {
    "nvim-lualine/lualine.nvim",
    event = "VeryLazy",
    opts = function(_, opts)
      -- remove time on status bar
      table.remove(opts.sections.lualine_z, 1)
    end,
  },
  {
    "neovim/nvim-lspconfig",
    opts = function(_, opts)
      -- disable inlay hints
      vim.list_extend(opts.inlay_hints, {
        enabled = false,
        exclude = {
          "dart",
        },
      })
    end,
  },
}
