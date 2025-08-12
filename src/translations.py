from PySide6.QtCore import QCoreApplication
from types import MappingProxyType
# 自訂庫
from src.classes.ui.lazy_str import LazyStr

# 翻譯類型
class _tr:
    def __init__(self):
        # 翻譯定義
        ## UI 固定字串
        self._UI_CONSTANTS = {
            # main_view
            "Onee Meta": LazyStr("Onee Meta", "ui_main_view"),
            # sendCritical
            "設定錯誤": LazyStr("設定錯誤", "ui_send_critical"),
            "沒有目標語言檔案": LazyStr("沒有目標語言檔案", "ui_send_critical"),
        }

        # 固定
        self._UI_CONSTANTS = MappingProxyType(self._UI_CONSTANTS)

    # 提取器
    
    @property
    def UI_CONSTANTS(self):
        return self._UI_CONSTANTS
    
TR = _tr() # 實例化
