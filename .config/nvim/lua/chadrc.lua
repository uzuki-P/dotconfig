-- This file  needs to have same structure as nvconfig.lua
-- https://github.com/NvChad/NvChad/blob/v2.5/lua/nvconfig.lua

---@type ChadrcConfig
local M = {}

M.ui = {
  theme = "one_light",
  theme_toggle = { "one_light", "one_light" },

  hl_override = {
    Comment = { italic = true },
    ["@comment"] = { italic = true },
    NvimTreeOpenedFolderName = { fg = "green", bold = true },
  },

  transparency = false,

  tabufline = {
    order = { "buffers", "tabs", "btns", "treeOffset" },
  },
}

return M
