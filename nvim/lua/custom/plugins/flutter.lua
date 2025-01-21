return {
  'nvim-flutter/flutter-tools.nvim',
  lazy = false,
  dependencies = {
    'nvim-lua/plenary.nvim',
    'stevearc/dressing.nvim', -- optional for vim.ui.select
  },
  config = true,
  opts = {
    decorations = {
      statusline = {
        app_version = true,
        device = true,
        project_config = true,
      },
    },
    debugger = {
      enabled = true,
      run_via_dap = true,
      register_configurations = function(_)
        require('dap').adapters.dart = {
          type = 'executable',
          command = 'dart',
          args = { 'debug_adapter' },
        }
        require('dap').adapters.flutter = {
          type = 'executable',
          command = 'flutter',
          args = { 'debug_adapter' },
        }
        require('dap').configurations.dart = {
          {
            type = 'flutter',
            request = 'launch',
            name = 'GIC V2',
            flutter_mode = 'staging',
            dartSdkPath = '/home/uzuki_p/.puro/envs/stable/flutter/bin/cache/dart-sdk/bin/dart',
            flutterSdkPath = '/home/uzuki_p/.puro/envs/stable/flutter/bin/flutter',
            program = '${workspaceFolder}/lib/main_staging.dart',
            cwd = '${workspaceFolder}',
            args = { '--flavor', 'staging' },
          },
          {
            type = 'flutter',
            request = 'launch',
            name = 'GIC V1',
            flutter_mode = 'staging',
            dartSdkPath = '/home/uzuki_p/.puro/envs/3.24.5/flutter/bin/cache/dart-sdk/bin/dart',
            flutterSdkPath = '/home/uzuki_p/.puro/envs/3.24.5/flutter/bin/flutter',
            program = '${workspaceFolder}/lib/main.dart',
            cwd = '${workspaceFolder}',
            args = { '--flavor', 'staging' },
          },
        }
        -- require('dap.ext.vscode').load_launchjs()
      end,
    },
    -- lsp = {
    --   on_attach = function(buf)
    --     local map = function(keys, func, desc, mode)
    --       mode = mode or 'n'
    --       vim.keymap.set(mode, keys, func, { buffer = buf, desc = 'LSP: ' .. desc })
    --     end
    --
    --     -- Jump to the definition of the word under your cursor.
    --     --  This is where a variable was first declared, or where a function is defined, etc.
    --     --  To jump back, press <C-t>.
    --     map('gd', require('telescope.builtin').lsp_definitions, '[G]oto [D]efinition')
    --
    --     -- Find references for the word under your cursor.
    --     map('gr', require('telescope.builtin').lsp_references, '[G]oto [R]eferences')
    --
    --     -- Jump to the implementation of the word under your cursor.
    --     --  Useful when your language has ways of declaring types without an actual implementation.
    --     map('gI', require('telescope.builtin').lsp_implementations, '[G]oto [I]mplementation')
    --
    --     -- Jump to the type of the word under your cursor.
    --     --  Useful when you're not sure what type a variable is and you want to see
    --     --  the definition of its *type*, not where it was *defined*.
    --     map('<leader>D', require('telescope.builtin').lsp_type_definitions, 'Type [D]efinition')
    --
    --     -- Fuzzy find all the symbols in your current document.
    --     --  Symbols are things like variables, functions, types, etc.
    --     map('<leader>ds', require('telescope.builtin').lsp_document_symbols, '[D]ocument [S]ymbols')
    --
    --     -- Fuzzy find all the symbols in your current workspace.
    --     --  Similar to document symbols, except searches over your entire project.
    --     map('<leader>ws', require('telescope.builtin').lsp_dynamic_workspace_symbols, '[W]orkspace [S]ymbols')
    --
    --     -- Rename the variable under your cursor.
    --     --  Most Language Servers support renaming across files, etc.
    --     map('<leader>rn', vim.lsp.buf.rename, '[R]e[n]ame')
    --
    --     -- Execute a code action, usually your cursor needs to be on top of an error
    --     -- or a suggestion from your LSP for this to activate.
    --     map('<leader>ca', vim.lsp.buf.code_action, '[C]ode [A]ction', { 'n', 'x' })
    --
    --     -- WARN: This is not Goto Definition, this is Goto Declaration.
    --     --  For example, in C this would take you to the header.
    --     map('gD', vim.lsp.buf.declaration, '[G]oto [D]eclaration')
    --   end,
    -- },
  },
}
