from PySide6.QtCore import QObject, QTranslator, QModelIndex
from PySide6.QtWidgets import QApplication
from typing import List
import os
# 自訂庫
from src.model.main_model import MainModel
from src.classes.data.comic_info_data import ComicInfoData
from src.view.main_view import MainView
from src.signal_bus import SIGNAL_BUS
from src.translations import TR
from src.controller.functions.string_process import resolve_placeholders

class MainController(QObject):
    """主控制
    """
    def __init__(self, model:MainModel, view: MainView, application: QApplication, translator: QTranslator) -> None:
        super().__init__()
        # 基本控件綁定
        self.model = model
        self.view = view
        self.application = application
        self.translator = translator

        # 訊號連結
        self.signal_connection()

    ##### 初始化函式

    def signal_connection(self) -> None:
        """訊號連接
        """
        # 應用功能
        SIGNAL_BUS.uiSend.selectComicFolder.connect(self.selectComicFolder) # 選擇漫畫資料夾
        SIGNAL_BUS.uiSend.selectComic.connect(self.selectComic) # 漫畫選擇
        SIGNAL_BUS.uiSend.start.connect(self.startProcess) # 開始處理
        # App設定
        SIGNAL_BUS.appSetting.fontSizeChanged.connect(self.changeFontSize) # 字體大小切換
        SIGNAL_BUS.appSetting.imageExtChanged.connect(self.changeImageExt) # 圖片附檔名設定
        SIGNAL_BUS.appSetting.allowFileChanged.connect(self.changeAllowFile) # 允許檔案設定
        SIGNAL_BUS.appSetting.langChanged.connect(self.changeLang) # 語言切換

    ##### 功能性函式

    ###### 應用功能

    def selectComic(self, comic: dict[str, QModelIndex]) -> None:
        """漫畫選擇

        Args:
            comic (dict[str, QModelIndex]): 漫畫
        """
        view = self.view.right_widget
        self.model.appStore.set("comic_select", comic) # 儲存選擇
        # 切換tab顯示狀態
        if len(comic) < 1:
            # 小於1，直接攔截
            view.tabs.setTabVisible(view.index_info_editor_tab, False)
            return
        changeVisible = view.tabs.isTabVisible(view.index_info_editor_tab)
        if not changeVisible:
            view.tabs.setTabVisible(view.index_info_editor_tab, True)
            view.tabs.setCurrentIndex(view.index_info_editor_tab)
        # 取得漫畫資料
        comic_info_list: List[ComicInfoData] = [
            self.model.comicStore.get(comicName) for comicName in comic.keys()
        ]
        # 設置編輯器顯示
        view.info_editor_tab.setComicInfoData(comic_info_list)


    def selectComicFolder(self, folder: str) -> None:
        """選擇漫畫資料夾

        Args:
            folder (str): 資料夾路徑
        """
        self.view.loading.show() # 顯示處理中
        self.model.appStore.set("comic_folder_path", folder) # 儲存設定
        self.view.left_widget.comic_path_button.setText(folder) # 改換按鈕文字
        self.view.left_widget.comic_path_button.setToolTip(folder) # 改換按鈕提示
        self.model.readComicFolder(folder) # 呼叫 model 讀取
        self.view.left_widget.comic_list.setComicList(self.model.appStore.get("comic_list", [])) # 設定顯示列表
        self.view.loading.close() # 關閉處理中

    def startProcess(self) -> None:
        """開始處理
        """
        self.view.loading.show() # 顯示處理中
        edit_data: ComicInfoData = self.view.right_widget.info_editor_tab.getComicInfoData() # 取得編輯資料
        comic_select: dict[str, QModelIndex] = self.model.appStore.get("comic_select", {}) # 取得選擇
        if not comic_select or len(comic_select) < 1:
            self.view.loading.close() # 關閉處理中
            return
        # 處理每一筆漫畫
        for comic_name, model_index in comic_select.items():
            if self.model.comicStore.get(comic_name) == None:
                continue
            comic_info_data: ComicInfoData = self.model.comicStore.get(comic_name)
            # 創建深度拷貝
            new_data: ComicInfoData = {
                "nsmap": comic_info_data.get("nsmap", {}).copy(),
                "fields": {
                    "base": comic_info_data.get("fields", {}).get("base", {}).copy()
                }
            }
            if "original_path" in comic_info_data:
                new_data["original_path"] = comic_info_data["original_path"]
            # 套用編輯資料
            for ns, fields in edit_data.get("fields", {}).items():
                if ns not in new_data["fields"]:
                    new_data["fields"][ns] = {}
                for field_name, value in fields.items():
                    if value == "{keep}" or value == None:
                        # 保持原值
                        continue
                    elif value == "":
                        # 清空值
                        if field_name in new_data["fields"][ns]:
                            del new_data["fields"][ns][field_name]
                    else:
                        # 設定新值
                        new_data["fields"][ns][field_name] = resolve_placeholders(value, {
                            "{index}": str(model_index.row() + 1),
                            "{total}": str(len(self.model.comicStore.data)),
                        })
            # 寫入檔案
            comic_folder_path = self.model.appStore.get("comic_folder_path", "")
            if comic_folder_path == "":
                continue
            comic_path = os.path.join(comic_folder_path, comic_name)
            
            


    ###### 應用設定

    def changeAllowFile(self, fileList: List[str]) -> None:
        """修改允許檔案設定

        Args:
            fileList (List[str]): 允許檔案列表
        """
        self.model.appSetting.set("allow_files", fileList)
        self.view.right_widget.app_setting_tab.allow_files_changed_display(fileList)

    def changeImageExt(self, extList: List[str]) -> None:
        """修改圖片副檔名設定

        Args:
            extList (List[str]): 副檔名列表
        """
        self.model.appSetting.set("image_exts", extList)
        self.view.right_widget.app_setting_tab.image_extension_changed_display(extList)

    def changeFontSize(self, size: int) -> None:
        """切換字體大小

        Args:
            size (int): 大小
        """
        self.model.appSetting.set("font_size", size)
        self.view.change_font_size(size)

    def changeLang(self, langName: str) -> None:
        """切換語言

        Args:
            langName (str): 語言名稱
        """
        lang_file = self.model.appStore.get("translation_files", {}).get(langName)
        # 沒有指定語言檔案
        if lang_file == None:
            self.model.appSetting.set("lang", "") # 儲存設定
            self.application.removeTranslator(self.translator) # 移除翻譯器
            SIGNAL_BUS.ui.retranslateUi.emit() # 呼叫刷新
            if langName != "": # 錯誤檢查
                SIGNAL_BUS.ui.sendCritical.emit(TR.UI_CONSTANTS["設定錯誤"](), TR.UI_CONSTANTS["沒有目標語言檔案"]())
            return
        # 有指定語言檔案
        self.model.appSetting.set("lang", langName) # 儲存設定
        self.translator.load(lang_file) # 加載翻譯器
        self.application.installTranslator(self.translator)
        SIGNAL_BUS.ui.retranslateUi.emit() # 呼叫刷新
