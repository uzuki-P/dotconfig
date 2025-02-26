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
    "saghen/blink.cmp",
    optional = true,
    opts = {
      snippets = {
        preset = "luasnip",
      },
    },
  },
  {
    "nvim-treesitter/nvim-treesitter",
    opts = {
      ensure_installed = {
        "bash",
        "html",
        "javascript",
        "json",
        "lua",
        "markdown",
        "markdown_inline",
        "query",
        "regex",
        "tsx",
        "typescript",
        "vim",
        "yaml",
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
            { id = "scopes", size = 1.05 }, -- Variables in scope
            { id = "stacks", size = 0.05 }, -- Call stack
            { id = "breakpoints", size = 0.1 }, -- Active breakpoints
            { id = "repl", size = 0.6 }, -- Debug console output
          },
          size = 0.3, -- % of the screen width
          position = "right",
        },
      },
    },
  },
}
