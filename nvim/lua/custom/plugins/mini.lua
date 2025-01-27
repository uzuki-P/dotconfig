return {
  { --  Check out: https://github.com/echasnovski/mini.nvim
    'echasnovski/mini.nvim',
    config = function()
      --  - va)  - [V]isually select [A]round [)]paren
      --  - yinq - [Y]ank [I]nside [N]ext [Q]uote
      --  - ci'  - [C]hange [I]nside [']quote
      require('mini.ai').setup { n_lines = 500 }

      -- - saiw) - [S]urround [A]dd [I]nner [W]ord [)]Paren
      -- - sd'   - [S]urround [D]elete [']quotes
      -- - sr)'  - [S]urround [R]eplace [)] [']
      require('mini.surround').setup()

      local statusline = require 'mini.statusline'
      statusline.setup { use_icons = vim.g.have_nerd_font }
      ---@diagnostic disable-next-line: duplicate-set-field
      statusline.section_location = function()
        return '%2l:%-2v'
      end

      require('mini.notify').setup()
      require('mini.move').setup()
      require('mini.pairs').setup()
      require('mini.cursorword').setup()
      require('mini.jump2d').setup()
      require('mini.icons').setup()
      require('mini.tabline').setup()
      require('mini.sessions').setup()

      require('mini.indentscope').setup {
        draw = {
          animation = require('mini.indentscope').gen_animation.none(),
        },
      }

      local starter = require 'mini.starter'
      starter.setup {
        header = function()
          return 'Apa carik wak???'
        end,
        query_updaters = 'abcdefghijklmnopqrstuvwxyz0123456789',
        -- items = {
        --   starter.sections.sessions(5, true),
        -- },
      }

      -- --- mini.files configuration
      -- local show_dotfiles = false
      --
      -- --- mini.files toggle dotfiles
      -- local filter_show = function(_)
      --   return true
      -- end
      --
      -- local filter_hide = function(fs_entry)
      --   return not vim.startswith(fs_entry.name, '.')
      -- end
      --
      -- local toggle_dotfiles = function()
      --   show_dotfiles = not show_dotfiles
      --   local new_filter = show_dotfiles and filter_show or filter_hide
      --   MiniFiles.refresh { content = { filter = new_filter } }
      -- end
      -- --- END mini.files toggle dotfiles
      --
      -- -- local files_set_cwd = function(_)
      -- --   -- Works only if cursor is on the valid file system entry
      -- --   local cur_entry_path = MiniFiles.get_fs_entry().path
      -- --   local cur_directory = vim.fs.dirname(cur_entry_path)
      -- --   vim.fn.chdir(cur_directory)
      -- -- end
      --
      -- --- mini.files open in split
      -- local map_split = function(buf_id, lhs, direction)
      --   local rhs = function()
      --     -- Make new window and set it as target
      --     local cur_target = MiniFiles.get_explorer_state().target_window
      --     local new_target = vim.api.nvim_win_call(cur_target, function()
      --       vim.cmd(direction .. ' split')
      --       return vim.api.nvim_get_current_win()
      --     end)
      --
      --     MiniFiles.set_target_window(new_target)
      --
      --     -- This intentionally doesn't act on file under cursor in favor of
      --     -- explicit "go in" action (`l` / `L`). To immediately open file,
      --     -- add appropriate `MiniFiles.go_in()` call instead of this comment.
      --   end
      --   --- END mini.files open in split
      --
      --   -- Adding `desc` will result into `show_help` entries
      --   local desc = 'Split ' .. direction
      --   vim.keymap.set('n', lhs, rhs, { buffer = buf_id, desc = desc })
      -- end
      --
      -- vim.api.nvim_create_autocmd('User', {
      --   pattern = 'MiniFilesBufferCreate',
      --   callback = function(args)
      --     local buf_id = args.data.buf_id
      --     vim.keymap.set('n', 'g.', toggle_dotfiles, { buffer = buf_id, desc = 'Show/Hide dotfiles' })
      --     -- vim.keymap.set('n', 'gcd', files_set_cwd, { buffer = buf_id, desc = 'Set [C]urrent working [D]irectory' })
      --     map_split(buf_id, '<C-h>', 'belowright horizontal')
      --     map_split(buf_id, '<C-v>', 'belowright vertical')
      --   end,
      -- })
      --
      -- require('mini.files').setup {
      --   content = { filter = filter_hide },
      --   options = {
      --     permanent_delete = false,
      --   },
      --   windows = {
      --     preview = true,
      --     width_preview = 100,
      --   },
      --   -- oil like mapping
      --   mappings = {
      --     go_in = '',
      --     go_in_plus = '<CR>',
      --     go_out = '-',
      --     go_out_plus = '',
      --     synchronize = '<C-S>',
      --   },
      -- }
      --
      -- local mini_files_open = function()
      --   -- Close explorer if it is opened
      --   -- if MiniFiles.close() then
      --   --   return
      --   -- end
      --
      --   -- Compute whether current buffer is for file on disk.
      --   -- If yes - use it to open explorer; otherwise use cwd.
      --   local buf_path = vim.api.nvim_buf_get_name(0)
      --   local path = vim.loop.fs_stat(buf_path) ~= nil and buf_path or vim.fn.getcwd()
      --   MiniFiles.open(path)
      -- end
      --
      -- vim.keymap.set('n', '-', mini_files_open, { desc = 'Open MiniFiles' })
      --
      -- --- END mini.files configuration
    end,
  },
}
-- vim: ts=2 sts=2 sw=2 et
