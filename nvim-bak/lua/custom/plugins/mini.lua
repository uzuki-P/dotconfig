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
      -- require('mini.operators').setup()

      require('mini.sessions').setup()
      vim.keymap.set('n', '<space>ns', MiniSessions.select, { desc = '[N]vim [S]essions' })

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
    end,
  },
}
-- vim: ts=2 sts=2 sw=2 et
