"""翻譯: 設定分頁 (app_setting_tab)"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

APP_SETTING_TAB = MappingProxyType({
    "字體大小：": LazyStr("字體大小：", "app_setting_tab"),
    "圖片附檔名：": LazyStr("圖片附檔名：", "app_setting_tab"),
    "允許檔案：": LazyStr("允許檔案：", "app_setting_tab"),
    "語言選擇：": LazyStr("語言選擇：", "app_setting_tab"),
    "Calibre路徑：": LazyStr("Calibre路徑：", "app_setting_tab"),
    "雙列表佈局：": LazyStr("雙列表佈局：", "app_setting_tab"),
    "關閉": LazyStr("關閉", "app_setting_tab"),
    "左右並排": LazyStr("左右並排", "app_setting_tab"),
    "上下垂直": LazyStr("上下垂直", "app_setting_tab"),
})
