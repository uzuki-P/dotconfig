return {
  'bgaillard/readonly.nvim',
  lazy = false,
  dependencies = {
    'rcarriga/nvim-notify',
  },
  opts = {
    -- see https://neovim.io/doc/user/lua.html#vim.fs.normalize()
    secured_files = {
      '~/%.aws/config',
      '~/%.aws/credentials',
      '~/%.ssh/.',
      '~/.puro/.',
    },
  },
}
