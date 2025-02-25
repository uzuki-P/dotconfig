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
    opts = {
      -- disable inlay hints
      inlay_hints = {
        enabled = false,
        -- exclude = {
        --   "dart",
        -- },
      },
    },
  },
  {
    "rcarriga/nvim-dap-ui",
    opts = {
      layouts = {
        {
          elements = {
            { id = "watches", size = 0.2 }, -- Watch expressions
            { id = "scopes", size = 0.1 }, -- Variables in scope
            { id = "stacks", size = 0.1 }, -- Call stack
            { id = "breakpoints", size = 0.1 }, -- Active breakpoints
            { id = "repl", size = 0.5 }, -- Debug console output
          },
          size = 0.2, -- 20% of the screen width
          position = "right",
        },
      },
    },
  },
}
