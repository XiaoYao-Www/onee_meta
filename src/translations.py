#####
# 翻譯主控器
#####
from PySide6.QtCore import QCoreApplication
from types import MappingProxyType
# 自訂庫
from src.classes.view.lazy_str import LazyStr


# 翻譯類型
class _tr:
    def __init__(self):
        #####
        # 主view
        #####
        self._MAIN_VIEW = {
            "Onee Meta": LazyStr("Onee Meta", "ui_main_view"),
            "處理中": LazyStr("處理中...", "ui_main_view"),
        }

        self._COMIC_LIST_VIEW = {
            "選擇漫畫資料夾路徑": LazyStr("選擇漫畫資料夾路徑", "comic_list_view"),
            "手動": LazyStr("手動", "comic_list_view"),
            "檔名": LazyStr("檔名", "comic_list_view"),
            "{selected} / {total} 本漫畫": LazyStr("{selected} / {total} 本漫畫", "comic_list_view"),
            "選擇漫畫資料夾": LazyStr("選擇漫畫資料夾", "comic_list_view"),
        }

        self._MAIN_CONTROLLER = {
            "設定錯誤": LazyStr("設定錯誤", "main_controller"),
            "沒有目標語言檔案": LazyStr("沒有目標語言檔案", "main_controller"),
        }

        self._OPERATION_AREA = {
            "儲存編輯": LazyStr("儲存編輯", "operation_area"),
            "關於": LazyStr("關於", "operation_area"),
            "設定": LazyStr("設定", "operation_area"),
        }

        self._APP_INFO_TAB = {
            "👻 作者資訊": LazyStr("👻 作者資訊", "app_info_tab"),
            "自我介紹": LazyStr(
                "逍遙 ( Xiao Yao )\n"
                "觀繁花而不與其爭艷\n"
                "處江湖而不染其煙塵", "app_info_tab"
            ),
            "作者 Github 連結": LazyStr("作者 Github 連結", "app_info_tab"),
            "📦 軟體資訊": LazyStr("📦 軟體資訊", "app_info_tab"),
            "軟體介紹": LazyStr(
                "版本: {version}\n"
                "姐姐大人永遠是對的", "app_info_tab"
            ),
            "專案 GitHub 專案連結": LazyStr("專案 GitHub 專案連結", "app_info_tab"),
        }

        self._APP_SETTING_TAB = {
            "字體大小：": LazyStr("字體大小：", "app_setting_tab"),
            "圖片附檔名：": LazyStr("圖片附檔名：", "app_setting_tab"),
            "允許檔案：": LazyStr("允許檔案：", "app_setting_tab"),
            "語言選擇：": LazyStr("語言選擇：", "app_setting_tab"),
        }


        self._UI_CONSTANTS = {
            # main_view
            "Onee Meta": LazyStr("Onee Meta", "ui_main_view"),
            "處理中...": LazyStr("處理中...", "ui_main_view"),
            # sendCritical
            "設定錯誤": LazyStr("設定錯誤", "ui_send_critical"),
            "沒有目標語言檔案": LazyStr("沒有目標語言檔案", "ui_send_critical"),
            # comic_list_view
            "選擇漫畫資料夾路徑": LazyStr("選擇漫畫資料夾路徑", "ui_comic_list_view"),
            "檔名": LazyStr("檔名", "ui_comic_list_view"),
            "手動": LazyStr("手動", "ui_comic_list_view"),
            "{selected} / {total} 本漫畫": LazyStr("{selected} / {total} 本漫畫", "ui_comic_list_view"),
            "選擇漫畫資料夾": LazyStr("選擇漫畫資料夾", "ui_comic_list_view"),
            # operation_area
            "儲存編輯": LazyStr("儲存編輯", "ui_operation_area"),
            "關於": LazyStr("關於", "ui_operation_area"),
            "設定": LazyStr("設定", "ui_operation_area"),
            "資訊": LazyStr("資訊", "ui_operation_area"),
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
            # info_editor_tab
            "輸入{keep}保留原值": LazyStr("輸入{keep}保留原值", "ui_info_editor_tab"),
        }
        ## 漫畫資訊編輯欄位設定
        self._INFO_EDITOR_TAB_CONFIG = {
            "書籍資訊": LazyStr("書籍資訊", "info_editor_tab_config"),
            "標題": LazyStr("標題", "info_editor_tab_config"),
            "系列名稱": LazyStr("系列名稱", "info_editor_tab_config"),
            "系列分組": LazyStr("系列分組", "info_editor_tab_config"),
            "風格類型": LazyStr("風格類型", "info_editor_tab_config"),
            "集數編號": LazyStr("集數編號", "info_editor_tab_config"),
            "總集數": LazyStr("總集數", "info_editor_tab_config"),
            "卷/冊號": LazyStr("卷/冊號", "info_editor_tab_config"),
            "頁數": LazyStr("頁數", "info_editor_tab_config"),
            "格式描述": LazyStr("格式描述", "info_editor_tab_config"),
            "語言 (ISO 639)": LazyStr("語言 (ISO 639)", "info_editor_tab_config"),
            "替代版本": LazyStr("替代版本", "info_editor_tab_config"),
            "替代系列名稱": LazyStr("替代系列名稱", "info_editor_tab_config"),
            "替代集數": LazyStr("替代集數", "info_editor_tab_config"),
            "替代總集數": LazyStr("替代總集數", "info_editor_tab_config"),
            "內容摘要": LazyStr("內容摘要", "info_editor_tab_config"),
            "簡介": LazyStr("簡介", "info_editor_tab_config"),
            "備註": LazyStr("備註", "info_editor_tab_config"),
            "評論": LazyStr("評論", "info_editor_tab_config"),
            "角色與劇情": LazyStr("角色與劇情", "info_editor_tab_config"),
            "登場角色": LazyStr("登場角色", "info_editor_tab_config"),
            "主角或主團隊": LazyStr("主角或主團隊", "info_editor_tab_config"),
            "故事主軸": LazyStr("故事主軸", "info_editor_tab_config"),
            "地點": LazyStr("地點", "info_editor_tab_config"),
            "出場團隊": LazyStr("出場團隊", "info_editor_tab_config"),
            "內容屬性": LazyStr("內容屬性", "info_editor_tab_config"),
            "黑白色彩": LazyStr("黑白色彩", "info_editor_tab_config"),
            "是否為漫畫": LazyStr("是否為漫畫", "info_editor_tab_config"),
            "年齡分級": LazyStr("年齡分級", "info_editor_tab_config"),
            "創作團隊": LazyStr("創作團隊", "info_editor_tab_config"),
            "作者": LazyStr("作者", "info_editor_tab_config"),
            "畫者 (鉛筆)": LazyStr("畫者 (鉛筆)", "info_editor_tab_config"),
            "墨線師": LazyStr("墨線師", "info_editor_tab_config"),
            "上色師": LazyStr("上色師", "info_editor_tab_config"),
            "字體設計": LazyStr("字體設計", "info_editor_tab_config"),
            "封面設計": LazyStr("封面設計", "info_editor_tab_config"),
            "編輯": LazyStr("編輯", "info_editor_tab_config"),
            "出版資訊": LazyStr("出版資訊", "info_editor_tab_config"),
            "出版社": LazyStr("出版社", "info_editor_tab_config"),
            "品牌 / 出版系列": LazyStr("品牌 / 出版系列", "info_editor_tab_config"),
            "網站": LazyStr("網站", "info_editor_tab_config"),
            "出版年": LazyStr("出版年", "info_editor_tab_config"),
            "出版月": LazyStr("出版月", "info_editor_tab_config"),
            "出版日": LazyStr("出版日", "info_editor_tab_config"),
            "掃描資訊": LazyStr("掃描資訊", "info_editor_tab_config"),
            "標籤": LazyStr("標籤", "info_editor_tab_config"),
        }

        # 固定
        self._MAIN_VIEW = MappingProxyType(self._MAIN_VIEW)
        self._COMIC_LIST_VIEW = MappingProxyType(self._COMIC_LIST_VIEW)
        self._MAIN_CONTROLLER = MappingProxyType(self._MAIN_CONTROLLER)
        self._OPERATION_AREA = MappingProxyType(self._OPERATION_AREA)
        self._APP_INFO_TAB = MappingProxyType(self._APP_INFO_TAB)
        self._APP_SETTING_TAB = MappingProxyType(self._APP_SETTING_TAB)

        self._UI_CONSTANTS = MappingProxyType(self._UI_CONSTANTS)
        self._INFO_EDITOR_TAB_CONFIG = MappingProxyType(self._INFO_EDITOR_TAB_CONFIG)

    # 提取器
    @property
    def MAIN_VIEW(self):
        return self._MAIN_VIEW
    
    @property
    def COMIC_LIST_VIEW(self):
        return self._COMIC_LIST_VIEW
    
    @property
    def MAIN_CONTROLLER(self):
        return self._MAIN_CONTROLLER
    
    @property
    def OPERATION_AREA(self):
        return self._OPERATION_AREA
    
    @property
    def APP_INFO_TAB(self):
        return self._APP_INFO_TAB
    
    @property
    def APP_SETTING_TAB(self):
        return self._APP_SETTING_TAB


    @property
    def UI_CONSTANTS(self):
        return self._UI_CONSTANTS
    
    @property
    def INFO_EDITOR_TAB_CONFIG(self):
        return self._INFO_EDITOR_TAB_CONFIG
    
TR = _tr() # 實例化
