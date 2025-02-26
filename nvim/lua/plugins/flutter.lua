return {
  "nvim-flutter/flutter-tools.nvim",
  lazy = false,
  ft = "dart",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "stevearc/dressing.nvim", -- optional for vim.ui.select
    -- 'artemave/workspace-diagnostics.nvim',
  },
  config = true,
  keys = {
    {
      "<leader>dfd",
      ":FlutterDebug<CR>",
      desc = "Flutter > Debug",
    },
    {
      "<leader>dfs",
      ":FlutterQuit<CR>",
      desc = "Flutter > Quit/Stop",
    },
    {
      "<leader>dfr",
      ":FlutterReload<CR>",
      desc = "Flutter > Hot Reload",
    },
    {
      "<leader>dfR",
      ":FlutterRestart<CR>",
      desc = "Flutter > Hot Restart",
    },
  },
  opts = {
    root_patterns = { ".git", "pubspec.yaml" },
    lsp = {
      settings = {
        showTodos = false,
        completeFunctionCalls = true,
        analysisExcludedFolders = { "/home/uzuki_p/.puro/envs/stable/flutter/bin/flutter" },
        renameFilesWithClasses = "prompt", -- "always"
        enableSnippets = false,
        updateImportsOnRename = true, -- Whether to update imports and other directives when files are renamed. Required for `FlutterRename` command.
      },

      -- on_attach = function(client, bufnr)
      --   require('workspace-diagnostics').populate_workspace_diagnostics(client, bufnr)
      -- end,
    },
    decorations = {
      statusline = {
        app_version = true,
        device = true,
        project_config = true,
      },
    },
    dev_log = {
      enabled = false,
      filter = nil, -- optional callback to filter the log
      -- takes a log_line as string argument; returns a boolean or nil;
      -- the log_line is only added to the output if the function returns true
      notify_errors = false, -- if there is an error whilst running then notify the user
      open_cmd = "15split", -- command to use to open the log buffer
      focus_on_open = true, -- focus on the newly opened log window
    },
    flutter_path = "/home/uzuki_p/.puro/envs/stable/flutter/bin/flutter",
    -- flutter_path = '/home/uzuki_p/.puro/envs/3.24.5/flutter/bin/flutter',
    debugger = {
      enabled = true,
      run_via_dap = true,
      exception_breakpoints = {},
      register_configurations = function(_)
        require("dap").adapters.dart = {
          type = "executable",
          command = "dart",
          args = { "debug_adapter" },
        }
        require("dap").adapters.flutter = {
          type = "executable",
          command = "flutter",
          args = { "debug_adapter" },
        }
        require("dap").configurations.dart = {
          {
            type = "flutter",
            request = "launch",
            name = "[Stable] main_staging.dart (Staging flavor)",
            flutter_mode = "staging",
            dartSdkPath = "/home/uzuki_p/.puro/envs/stable/flutter/bin/cache/dart-sdk/bin/dart",
            flutterSdkPath = "/home/uzuki_p/.puro/envs/stable/flutter/bin/flutter",
            program = "${workspaceFolder}/lib/main_staging.dart",
            cwd = "${workspaceFolder}",
            args = { "--flavor", "staging" },
          },
          {
            type = "flutter",
            request = "launch",
            name = "[3.24.5] main.dart (Staging flavor)",
            flutter_mode = "staging",
            dartSdkPath = "/home/uzuki_p/.puro/envs/3.24.5/flutter/bin/cache/dart-sdk/bin/dart",
            flutterSdkPath = "/home/uzuki_p/.puro/envs/3.24.5/flutter/bin/flutter",
            program = "${workspaceFolder}/lib/main.dart",
            cwd = "${workspaceFolder}",
            args = { "--flavor", "staging" },
          },
          {
            type = "flutter",
            request = "launch",
            name = "[Stable] main_staging.dart (no flavor)",
            -- flutter_mode = "staging",
            dartSdkPath = "/home/uzuki_p/.puro/envs/stable/flutter/bin/cache/dart-sdk/bin/dart",
            flutterSdkPath = "/home/uzuki_p/.puro/envs/stable/flutter/bin/flutter",
            program = "${workspaceFolder}/lib/main_staging.dart",
            cwd = "${workspaceFolder}",
            -- args = { "--flavor", "staging" },
          },
        }
        -- require('dap.ext.vscode').load_launchjs()
      end,
    },
  },
}
