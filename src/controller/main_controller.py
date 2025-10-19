#####
# 主控制器
#####
from PySide6.QtCore import QObject, QTranslator, QModelIndex, QItemSelectionModel
from PySide6.QtWidgets import QApplication
from typing import List, cast
import os
import copy
# 自訂庫
from src.model.main_model import MainModel
from src.view.main_view import MainView
from src.signal_bus import SIGNAL_BUS
from src.translations import TR
from src.classes.model.comic_data import XmlComicInfo, ComicData
from src.classes.controller.comic_placeholder_data import ComicPlaceholderData
from src.controller.functions.placeholder_process import XmlDataPlaceholderProcess
from src.controller.functions.xml_data_process import updataXmlComicInfo

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

        # 應用初始化
        self.application_init()

    ### 初始化函式 ###

    def application_linkage_structure(self) -> None:
        """應用連結構建
        """
        self.view.left_widget.setListModel(self.model.comicListModel) # 漫畫列表模型

    def application_init(self) -> None:
        """應用初始化
        """
        # 設定選項注入
        self.view.right_widget.app_setting_tab.lang_select_combo.clear() # 清除選項
        lang_select_items: list[str] = list(self.model.runningStore.get("translation_files", {}).keys()) # 取得鍵
        lang_select_items.insert(0, "") # 添加預設選項
        self.view.right_widget.app_setting_tab.lang_select_combo.addItems(
            lang_select_items
        )
        # 設定初始化
        self.setAppFontSize(self.model.appSetting.get("font_size", 10)) # 字體大小
        self.setImageExt(self.model.appSetting.get("image_exts", [])) # 圖片副檔名
        self.setAllowFile(self.model.appSetting.get("allow_files", [])) # 允許檔案
        self.changeLang(self.model.appSetting.get("lang", "")) # 翻譯


    def signal_connection(self) -> None:
        """訊號連接
        """
        # 應用功能
        SIGNAL_BUS.uiSend.selectComicFolder.connect(self.selectComicFolder) # 選擇漫畫資料夾
        SIGNAL_BUS.uiSend.comicListSelected.connect(self.selectComic) # 漫畫選擇
        SIGNAL_BUS.uiSend.startProcess.connect(self.startProcess) # 開始處理
        # 應用設定
        SIGNAL_BUS.uiSend.fontSizeSet.connect(self.setAppFontSize) # 字體大小切換
        SIGNAL_BUS.uiSend.imgExtensionSet.connect(self.setImageExt) # 圖片附檔名設定
        SIGNAL_BUS.uiSend.allowFileSet.connect(self.setAllowFile) # 允許檔案設定
        SIGNAL_BUS.uiSend.langChange.connect(self.changeLang) # 語言切換
        # 連接功能
        self.model.comicListModel.listIndexChange = self.comicListIndexChanged # 漫畫排列後選擇

    ### 功能性函 ###

    ###### 應用功能

    def selectComic(self, comic: list[int]) -> None:
        """漫畫選擇

        Args:
            comic (list[int]): 漫畫
        """
        operationArea = self.view.right_widget
        # 切換tab顯示狀態
        if len(comic) < 1:
            # 小於1，直接攔截
            operationArea.tabs.setTabVisible(operationArea.index_info_editor_tab, False)
            return
        changeVisible = operationArea.tabs.isTabVisible(operationArea.index_info_editor_tab)
        if not changeVisible:
            operationArea.tabs.setTabVisible(operationArea.index_info_editor_tab, True)
            operationArea.tabs.setCurrentIndex(operationArea.index_info_editor_tab)
        # 設置資訊編輯器
        uuidList: list[str] = self.model.runningStore.get("comic_uuid_list", []) # 取得漫畫uuid總列表
        selectedUuids: list[str] = [uuidList[listIndex] for listIndex in comic] # 選中漫畫UUID列表
        self.model.runningStore.set("selected_comics", selectedUuids) # 儲存選中UUID
        xmlComicDataList: list[XmlComicInfo] = [
            cast(ComicData, self.model.comicDataStore.get(uuid)).get("xml_comic_info") for uuid in selectedUuids
            ] # 選中漫畫資料列表
        self.view.right_widget.info_editor_tab.setComicInfoData(xmlComicDataList) # 填充顯示


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

    def startProcess(self) -> None:
        """開始處理
        """
        self.view.loading.show() # 顯示處理中
        editer_data: XmlComicInfo = self.view.right_widget.info_editor_tab.getComicInfoData() # 取得編輯資料
        uuid_select: list[str] = self.model.runningStore.get("selected_comics", []) # 取得選擇
        comic_all_list: list[str] = self.model.runningStore.get("comic_uuid_list", []) # 當前漫畫列表
        if not uuid_select or len(uuid_select) < 1 or not comic_all_list or len(comic_all_list) < 1:
            self.view.loading.close() # 關閉處理中
            return
        # 處理每一筆漫畫
        for order, uuid in enumerate(uuid_select, start= 1):
            # 組合佔位符資料
            placeholder: ComicPlaceholderData = {
                "index": comic_all_list.index(uuid) + 1,
                "order": order,
            }
            # 創建針對性Xml資料
            placeholder_editer_data: XmlComicInfo = XmlDataPlaceholderProcess(editer_data, placeholder)
            # 更新Xml資料
            old_xml_data: XmlComicInfo = cast(ComicData, self.model.comicDataStore.get(uuid)).get("xml_comic_info")
            if old_xml_data == None:
                continue
            backup_xml_data: XmlComicInfo = copy.deepcopy(old_xml_data) # 先備份
            updataXmlComicInfo(old_xml_data, placeholder_editer_data)
            # 寫入檔案
            if not(self.model.writeComic(uuid)):
                # 寫入失敗時恢復資料
                comic_data = cast(ComicData, self.model.comicDataStore.get(uuid))["xml_comic_info"] = backup_xml_data

        self.model.comicListModel.layoutChanged.emit() # 呼叫刷新列表顯示
        self.view.left_widget.setSortType(0) # 改變排序方式
        self.view.loading.close() # 關閉處理中



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

    def setAllowFile(self, fileList: List[str]) -> None:
        """設置允許檔案設定

        Args:
            fileList (List[str]): 允許檔案列表
        """
        self.model.appSetting.set("allow_files", fileList) # 修改設定
        self.view.right_widget.app_setting_tab.allowFilesChangedDisplay(fileList) # 顯示調整

    def setImageExt(self, extList: List[str]) -> None:
        """設置圖片副檔名設定

        Args:
            extList (List[str]): 副檔名列表
        """
        self.model.appSetting.set("image_exts", extList) # 修改設定
        self.view.right_widget.app_setting_tab.imageExtensionChangedDisplay(extList) # 顯示調整

    def setAppFontSize(self, size: int) -> None:
        """設置字體大小

        Args:
            size (int): 大小
        """
        self.model.appSetting.set("font_size", size) # 修改設定
        self.view.changeFontSize(size) # 設定執行
        self.view.right_widget.app_setting_tab.fontSizeChangedDisplay(size) # 顯示調整

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
            self.view.right_widget.app_setting_tab.langSelectedChangedDisplay("") # 顯示調整
            return
        # 有指定語言檔案
        self.model.appSetting.set("lang", langName) # 儲存設定
        self.translator.load(lang_file) # 加載翻譯器
        self.application.installTranslator(self.translator)
        SIGNAL_BUS.uiRevice.translateUi.emit() # 呼叫刷新
        self.view.right_widget.app_setting_tab.langSelectedChangedDisplay(langName) # 顯示調整