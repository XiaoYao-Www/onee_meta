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
            # comic_list_view
            "選擇漫畫資料夾路徑": LazyStr("選擇漫畫資料夾路徑", "ui_comic_list_view"),
            "檔名": LazyStr("檔名", "ui_comic_list_view"),
            "手動": LazyStr("手動", "ui_comic_list_view"),
            "{selected} / {total} 本漫畫": LazyStr("{selected} / {total} 本漫畫", "ui_comic_list_view"),
            # operation_area
            "儲存編輯": LazyStr("儲存編輯", "ui_operation_area"),
            "關於": LazyStr("關於", "ui_operation_area"),
            "設定": LazyStr("設定", "ui_operation_area"),
            # app_info_tab
            "👻 作者資訊": LazyStr("👻 作者資訊", "ui_app_info_tab"),
            "自我介紹": LazyStr(
                "逍遙 ( Xiao Yao )\n"
                "觀繁花而不與其爭艷\n"
                "處江湖而不染其煙塵", "ui_app_info_tab"
            ),
            "作者 Github 連結": LazyStr("作者 Github 連結", "ui_app_info_tab"),
            "📦 軟體資訊": LazyStr("📦 軟體資訊", "ui_app_info_tab"),
            "軟體介紹": LazyStr(
                "版本: {version}\n"
                "姐姐大人永遠是對的", "ui_app_info_tab"
            ),
            "專案 GitHub 專案連結": LazyStr("專案 GitHub 專案連結", "ui_app_info_tab"),
            # app_setting_tab
            "字體大小：": LazyStr("字體大小：", "ui_app_setting_tab"),
            "圖片附檔名：": LazyStr("圖片附檔名：", "ui_app_setting_tab"),
            "允許檔案：": LazyStr("允許檔案：", "ui_app_setting_tab"),
            "語言選擇：": LazyStr("語言選擇：", "ui_app_setting_tab"),
        }

        # 固定
        self._UI_CONSTANTS = MappingProxyType(self._UI_CONSTANTS)

    # 提取器
    
    @property
    def UI_CONSTANTS(self):
        return self._UI_CONSTANTS
    
TR = _tr() # 實例化
