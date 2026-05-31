"""翻譯: 主視窗 (main_view)"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

MAIN_VIEW = MappingProxyType({
    "Onee Meta": LazyStr("Onee Meta", "ui_main_view"),
    "處理中": LazyStr("處理中...", "ui_main_view"),
})
