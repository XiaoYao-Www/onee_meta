"""翻譯: 主控制器 (main_controller)"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

MAIN_CONTROLLER = MappingProxyType({
    "設定錯誤": LazyStr("設定錯誤", "main_controller"),
    "沒有目標語言檔案": LazyStr("沒有目標語言檔案", "main_controller"),
})
