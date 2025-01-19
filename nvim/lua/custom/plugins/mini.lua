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

      require('mini.indentscope').setup {
        draw = {
          animation = require('mini.indentscope').gen_animation.none(),
        },
      }

      require('mini.starter').setup {
        header = function()
          return 'Apa carik wak???'
        end,
      }

      --- mini.files configuration
      local show_dotfiles = true

      local filter_show = function(_)
        return true
      end

      local filter_hide = function(fs_entry)
        return not vim.startswith(fs_entry.name, '.')
      end

      local toggle_dotfiles = function()
        show_dotfiles = not show_dotfiles
        local new_filter = show_dotfiles and filter_show or filter_hide
        MiniFiles.refresh { content = { filter = new_filter } }
      end

      local files_set_cwd = function(_)
        -- Works only if cursor is on the valid file system entry
        local cur_entry_path = MiniFiles.get_fs_entry().path
        local cur_directory = vim.fs.dirname(cur_entry_path)
        vim.fn.chdir(cur_directory)
      end

      vim.api.nvim_create_autocmd('User', {
        pattern = 'MiniFilesBufferCreate',
        callback = function(args)
          local buf_id = args.data.buf_id
          -- Tweak left-hand side of mapping to your liking
          vim.keymap.set('n', 'g.', toggle_dotfiles, { buffer = buf_id, desc = 'Show/Hide dotfiles' })
          vim.keymap.set('n', 'g~', files_set_cwd, { buffer = args.data.buf_id })
        end,
      })

      require('mini.files').setup {
        options = {
          permanent_delete = false,
        },
        windows = {
          preview = true,
          width_preview = 100,
        },
      }
      --- END mini.files configuration
    end,
  },
}
-- vim: ts=2 sts=2 sw=2 et
