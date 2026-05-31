"""
UI 佈局常數 — 集中管理所有硬編碼尺寸

所有視窗、分割器、網格相關的魔術數字統一在此定義。
"""
from typing import Tuple

# ── 主視窗 ─────────────────────────────────────────────

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 750
DEFAULT_FONT_SIZE = 10

# ── Splitter 比例 ──────────────────────────────────────

# 主視窗左右分割 (漫畫列表 : 操作區)
MAIN_SPLITTER_SIZES: Tuple[int, int] = (200, 500)

# 資訊編輯器左右分割 (編輯區 : 側邊欄)
EDITOR_SPLITTER_SIZES: Tuple[int, int] = (900, 100)

# ── Sidebar ────────────────────────────────────────────

SIDEBAR_WIDTH = 250

# ── DataCard ───────────────────────────────────────────

TAG_GRID_MAX_COLUMNS = 5

# ── LoadingDialog ──────────────────────────────────────

LOADING_DIALOG_WIDTH = 200
LOADING_DIALOG_HEIGHT = 100
