from PySide6.QtCore import QObject, QTranslator, QModelIndex, QItemSelectionModel
from PySide6.QtWidgets import QApplication
from typing import List
import os
# 自訂庫
from src.model.main_model import MainModel
from src.view.main_view import MainView
from src.signal_bus import SIGNAL_BUS
from src.translations import TR

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

        # 應用連結構建
        self.application_linkage_structure()

        # 訊號連結
        self.signal_connection()

    ### 初始化函式 ###

    def application_linkage_structure(self) -> None:
        """應用連結構建
        """
        self.view.left_widget.setListModel(self.model.comicListModel) # 漫畫列表模型

    def signal_connection(self) -> None:
        """訊號連接
        """
        # 應用功能
        SIGNAL_BUS.uiSend.selectComicFolder.connect(self.selectComicFolder) # 選擇漫畫資料夾
        # SIGNAL_BUS.uiSend.selectComic.connect(self.selectComic) # 漫畫選擇
        # SIGNAL_BUS.uiSend.start.connect(self.startProcess) # 開始處理
        # App設定
        # SIGNAL_BUS.appSetting.fontSizeChanged.connect(self.changeFontSize) # 字體大小切換
        # SIGNAL_BUS.appSetting.imageExtChanged.connect(self.changeImageExt) # 圖片附檔名設定
        # SIGNAL_BUS.appSetting.allowFileChanged.connect(self.changeAllowFile) # 允許檔案設定
        # SIGNAL_BUS.appSetting.langChanged.connect(self.changeLang) # 語言切換
        # 連接功能
        self.model.comicListModel.listIndexChange = self.comicListIndexChanged # 漫畫排列後選擇

    ### 功能性函 ###

    ###### 應用功能

    # def selectComic(self, comic: dict[str, QModelIndex]) -> None:
    #     """漫畫選擇

    #     Args:
    #         comic (dict[str, QModelIndex]): 漫畫
    #     """
    #     view = self.view.right_widget
    #     self.model.appStore.set("comic_select", comic) # 儲存選擇
    #     # 切換tab顯示狀態
    #     if len(comic) < 1:
    #         # 小於1，直接攔截
    #         view.tabs.setTabVisible(view.index_info_editor_tab, False)
    #         return
    #     changeVisible = view.tabs.isTabVisible(view.index_info_editor_tab)
    #     if not changeVisible:
    #         view.tabs.setTabVisible(view.index_info_editor_tab, True)
    #         view.tabs.setCurrentIndex(view.index_info_editor_tab)
    #     # 取得漫畫資料
    #     comic_info_list: List[ComicInfoData] = [
    #         self.model.comicStore.get(comicName) for comicName in comic.keys()
    #     ]
    #     # 設置編輯器顯示
    #     view.info_editor_tab.setComicInfoData(comic_info_list)


    def selectComicFolder(self, folder: str) -> None:
        """選擇漫畫資料夾

        Args:
            folder (str): 資料夾路徑
        """
        self.view.loading.show() # 顯示處理中
        self.model.runningStore.set("comic_folder_path", folder) # 儲存設定
        self.view.left_widget.comic_path_button.setText(folder) # 改換按鈕文字
        self.view.left_widget.comic_path_button.setToolTip(folder) # 改換按鈕提示
        self.model.readComicFolder(folder) # 呼叫 model 讀取
        self.view.left_widget.changeInfoLabel(select=0 ,total=len(self.model.runningStore.get("comic_uuid_list", []))) # 設置顯示資料
        self.view.loading.close() # 關閉處理中

    # def startProcess(self) -> None:
    #     """開始處理
    #     """
    #     self.view.loading.show() # 顯示處理中
    #     edit_data: ComicInfoData = self.view.right_widget.info_editor_tab.getComicInfoData() # 取得編輯資料
    #     comic_select: dict[str, QModelIndex] = self.model.appStore.get("comic_select", {}) # 取得選擇
    #     if not comic_select or len(comic_select) < 1:
    #         self.view.loading.close() # 關閉處理中
    #         return
    #     # 處理每一筆漫畫
    #     for comic_name, model_index in comic_select.items():
    #         if self.model.comicStore.get(comic_name) == None:
    #             continue
    #         comic_info_data: ComicInfoData = self.model.comicStore.get(comic_name)
    #         # 創建深度拷貝
    #         new_data: ComicInfoData = {
    #             "nsmap": comic_info_data.get("nsmap", {}).copy(),
    #             "fields": {
    #                 "base": comic_info_data.get("fields", {}).get("base", {}).copy()
    #             }
    #         }
    #         if "original_path" in comic_info_data:
    #             new_data["original_path"] = comic_info_data["original_path"]
    #         # 套用編輯資料
    #         for ns, fields in edit_data.get("fields", {}).items():
    #             if ns not in new_data["fields"]:
    #                 new_data["fields"][ns] = {}
    #             for field_name, value in fields.items():
    #                 if value == "{keep}" or value == None:
    #                     # 保持原值
    #                     continue
    #                 elif value == "":
    #                     # 清空值
    #                     if field_name in new_data["fields"][ns]:
    #                         del new_data["fields"][ns][field_name]
    #                 else:
    #                     # 設定新值
    #                     new_data["fields"][ns][field_name] = resolve_placeholders(value, {
    #                         "{index}": str(model_index.row() + 1),
    #                         "{total}": str(len(self.model.comicStore.data)),
    #                     })
    #         # 寫入檔案
    #         comic_folder_path = self.model.appStore.get("comic_folder_path", "")
    #         if comic_folder_path == "":
    #             continue
    #         comic_path = os.path.join(comic_folder_path, comic_name)

    ###### 連接功能

    def comicListIndexChanged(self, uuidList: list[str]) -> None:
        """漫畫列表順序變動

        Args:
            uuidList (list[str]): UUID列表
        """
        # 重新設置選擇
        selectModel = self.view.left_widget.comic_list.selectionModel()
        selectModel.clearSelection()  # 清除舊選取

        for uuid in uuidList:
            try:
                row = self.model.comicListModel.uuidList.index(uuid)
            except ValueError:
                continue  # 找不到就跳過
            index = self.model.comicListModel.index(row)
            selectModel.select(index, QItemSelectionModel.SelectionFlag.Select)
        # 切換排序設定
        self.view.left_widget.setSortType(0) # 手動

    ###### 應用設定

    def changeAllowFile(self, fileList: List[str]) -> None:
        """修改允許檔案設定

        Args:
            fileList (List[str]): 允許檔案列表
        """
        self.model.appSetting.set("allow_files", fileList)

    def changeImageExt(self, extList: List[str]) -> None:
        """修改圖片副檔名設定

        Args:
            extList (List[str]): 副檔名列表
        """
        self.model.appSetting.set("image_exts", extList)

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
        lang_file = self.model.runningStore.get("translation_files", {}).get(langName)
        # 沒有指定語言檔案
        if lang_file == None:
            self.model.appSetting.set("lang", "") # 儲存設定
            self.application.removeTranslator(self.translator) # 移除翻譯器
            SIGNAL_BUS.uiRevice.translateUi.emit() # 呼叫刷新
            if langName != "": # 錯誤檢查
                SIGNAL_BUS.uiRevice.sendCritical.emit(TR.MAIN_CONTROLLER["設定錯誤"](), TR.MAIN_CONTROLLER["沒有目標語言檔案"]())
            return
        # 有指定語言檔案
        self.model.appSetting.set("lang", langName) # 儲存設定
        self.translator.load(lang_file) # 加載翻譯器
        self.application.installTranslator(self.translator)
        SIGNAL_BUS.uiRevice.translateUi.emit() # 呼叫刷新
