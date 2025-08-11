from PySide6.QtCore import QCoreApplication
from types import MappingProxyType
# 自訂庫
from src.classes.ui.lazy_str import LazyStr

# 翻譯類型
class _tr:
    def __init__(self):
        # 翻譯定義
        ## 漫畫資訊編輯欄位設定
        self._SCHEMA_CONFIG = {
            "書籍資訊": LazyStr("書籍資訊", "schema_config"),
            "標題": LazyStr("標題", "schema_config"),
            "系列名稱": LazyStr("系列名稱", "schema_config"),
            "系列分組": LazyStr("系列分組", "schema_config"),
            "風格類型": LazyStr("風格類型", "schema_config"),
            "集數編號": LazyStr("集數編號", "schema_config"),
            "總集數": LazyStr("總集數", "schema_config"),
            "卷/冊號": LazyStr("卷/冊號", "schema_config"),
            "頁數": LazyStr("頁數", "schema_config"),
            "格式描述": LazyStr("格式描述", "schema_config"),
            "語言 (ISO 639)": LazyStr("語言 (ISO 639)", "schema_config"),
            "替代版本": LazyStr("替代版本", "schema_config"),
            "替代系列名稱": LazyStr("替代系列名稱", "schema_config"),
            "替代集數": LazyStr("替代集數", "schema_config"),
            "替代總集數": LazyStr("替代總集數", "schema_config"),
            "內容摘要": LazyStr("內容摘要", "schema_config"),
            "簡介": LazyStr("簡介", "schema_config"),
            "備註": LazyStr("備註", "schema_config"),
            "評論": LazyStr("評論", "schema_config"),
            "角色與劇情": LazyStr("角色與劇情", "schema_config"),
            "登場角色": LazyStr("登場角色", "schema_config"),
            "主角或主團隊": LazyStr("主角或主團隊", "schema_config"),
            "故事主軸": LazyStr("故事主軸", "schema_config"),
            "地點": LazyStr("地點", "schema_config"),
            "出場團隊": LazyStr("出場團隊", "schema_config"),
            "內容屬性": LazyStr("內容屬性", "schema_config"),
            "黑白色彩": LazyStr("黑白色彩", "schema_config"),
            "是否為漫畫": LazyStr("是否為漫畫", "schema_config"),
            "年齡分級": LazyStr("年齡分級", "schema_config"),
            "創作團隊": LazyStr("創作團隊", "schema_config"),
            "作者": LazyStr("作者", "schema_config"),
            "畫者 (鉛筆)": LazyStr("畫者 (鉛筆)", "schema_config"),
            "墨線師": LazyStr("墨線師", "schema_config"),
            "上色師": LazyStr("上色師", "schema_config"),
            "字體設計": LazyStr("字體設計", "schema_config"),
            "封面設計": LazyStr("封面設計", "schema_config"),
            "編輯": LazyStr("編輯", "schema_config"),
            "出版資訊": LazyStr("出版資訊", "schema_config"),
            "出版社": LazyStr("出版社", "schema_config"),
            "品牌 / 出版系列": LazyStr("品牌 / 出版系列", "schema_config"),
            "網站": LazyStr("網站", "schema_config"),
            "出版年": LazyStr("出版年", "schema_config"),
            "出版月": LazyStr("出版月", "schema_config"),
            "出版日": LazyStr("出版日", "schema_config"),
            "掃描資訊": LazyStr("掃描資訊", "schema_config"),
            "標籤": LazyStr("標籤", "schema_config"),
        }
        ## UI 固定字串
        self._UI_CONSTANTS = {
            # main_view
            "Onee Meta": LazyStr("Onee Meta", "ui_main_view"),
            #########
            # main_window
            "ComicInfo 編輯器": LazyStr("ComicInfo 編輯器", "ui_constants"),
            "列表": LazyStr("列表", "ui_constants"),
            "編輯": LazyStr("編輯", "ui_constants"),
            "設定": LazyStr("設定", "ui_constants"),
            "關於": LazyStr("關於", "ui_constants"),
            "標籤": LazyStr("標籤", "ui_constants"),
            # app_info_tab
            "👻 作者資訊": LazyStr("👻 作者資訊", "ui_constants"),
            "自我介紹": LazyStr(
                "逍遙 ( Xiao Yao )\n"
                "觀繁花而不與其爭艷\n"
                "處江湖而不染其煙塵", "ui_constants"
            ),
            "作者 Github 連結": LazyStr("作者 Github 連結", "ui_constants"),
            "📦 軟體資訊": LazyStr("📦 軟體資訊", "ui_constants"),
            "軟體介紹": LazyStr(
                "版本: {version}\n"
                "一款用於編輯漫畫 ComicInfo 的編輯器", "ui_constants"
            ),
            "GitHub 專案連結": LazyStr("GitHub 專案連結", "ui_constants"),
            # app_setting_tab
            "字體大小：": LazyStr("字體大小：", "ui_constants"),
            "寫入模式：": LazyStr("寫入模式：", "ui_constants"),
            "原位置寫入": LazyStr("原位置寫入", "ui_constants"),
            "鋪平寫入": LazyStr("鋪平寫入", "ui_constants"),
            "圖片附檔名：": LazyStr("圖片附檔名：", "ui_constants"),
            "允許檔案：": LazyStr("允許檔案：", "ui_constants"),
            "語言選擇：": LazyStr("語言選擇：", "ui_constants"),
            # comics_list_tab
            "選擇漫畫資料夾": LazyStr("選擇漫畫資料夾", "ui_constants"),
            "尚未選擇": LazyStr("尚未選擇", "ui_constants"),
            "手動": LazyStr("手動", "ui_constants"),
            "檔名": LazyStr("檔名", "ui_constants"),
            "編號": LazyStr("編號", "ui_constants"),
            "排序依據：": LazyStr("排序依據：", "ui_constants"),
            "已選中 {selected} / 共 {total} 本漫畫": LazyStr("已選中 {selected} / 共 {total} 本漫畫", "ui_constants"),
            "選擇輸出資料夾": LazyStr("選擇輸出資料夾", "ui_constants"),
            "尚未選擇": LazyStr("尚未選擇", "ui_constants"),
            "輸出副檔名：": LazyStr("輸出副檔名：", "ui_constants"),
            "開始處理": LazyStr("開始處理", "ui_constants"),
            "選擇漫畫資料夾": LazyStr("選擇漫畫資料夾", "ui_constants"),
            "選擇輸出資料夾": LazyStr("選擇輸出資料夾", "ui_constants"),
        }

        self._SEND_MESSAGE = {
            "錯誤": LazyStr("錯誤", "send_message"),
            "提示": LazyStr("提示", "send_message"),
            "完成": LazyStr("完成", "send_message"),
            "請選擇輸出資料夾": LazyStr("請選擇輸出資料夾", "send_message"),
            "請選擇漫畫資料夾": LazyStr("請選擇漫畫資料夾", "send_message"),
            "請至少選擇一個檔案進行處理": LazyStr("請至少選擇一個檔案進行處理", "send_message"),
            "所有漫畫處理完成！": LazyStr("所有漫畫處理完成！", "send_message"),
        }

        # 固定
        self._SCHEMA_CONFIG = MappingProxyType(self._SCHEMA_CONFIG)
        self._UI_CONSTANTS = MappingProxyType(self._UI_CONSTANTS)
        self._SEND_MESSAGE = MappingProxyType(self._SEND_MESSAGE)

    # 提取器
    @property
    def SCHEMA_CONFIG(self):
        return self._SCHEMA_CONFIG
    
    @property
    def UI_CONSTANTS(self):
        return self._UI_CONSTANTS
    
    @property
    def SEND_MESSAGE(self):
        return self._SEND_MESSAGE
    
TR = _tr() # 實例化
