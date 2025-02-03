return {
  {
    'petertriho/nvim-scrollbar',
    opts = {},
    config = function()
      -- require('hlslens').setup() is not required
      require('scrollbar.handlers.search').setup {
        -- hlslens config overrides
      }
    end,
    dependencies = {
      {
        'kevinhwang91/nvim-hlslens',
        opts = {
          build_position_cb = function(plist, _, _, _)
            require('scrollbar.handlers.search').handler.show(plist.start_pos)
          end,
        },
      },
    },
  },
}
