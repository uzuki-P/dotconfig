return {
  'nvim-flutter/flutter-tools.nvim',
  lazy = false,
  dependencies = {
    'nvim-lua/plenary.nvim',
    'stevearc/dressing.nvim', -- optional for vim.ui.select
  },
  config = true,
  opts = {
    lsp = {
      settings = {
        showTodos = false,
      },
    },
    decorations = {
      statusline = {
        app_version = true,
        device = true,
        project_config = true,
      },
    },
    flutter_path = '/home/uzuki_p/.puro/envs/stable/flutter/bin/flutter',
    -- flutter_path = '/home/uzuki_p/.puro/envs/3.24.5/flutter/bin/flutter',
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
  },
}
