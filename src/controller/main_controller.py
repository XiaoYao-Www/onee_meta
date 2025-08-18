from PySide6.QtCore import QObject, QTranslator
from PySide6.QtWidgets import QApplication
from typing import List
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

        # 訊號連結
        self.signal_connection()

    ##### 初始化函式

    def signal_connection(self) -> None:
        """訊號連接
        """
        # 應用功能
        SIGNAL_BUS.uiSend.selectComicFolder.connect(self.selectComicFolder) # 選擇漫畫資料夾
        # App設定
        SIGNAL_BUS.appSetting.fontSizeChanged.connect(self.changeFontSize) # 字體大小切換
        SIGNAL_BUS.appSetting.imageExtChanged.connect(self.changeImageExt) # 圖片附檔名設定
        SIGNAL_BUS.appSetting.allowFileChanged.connect(self.changeAllowFile) # 允許檔案設定
        SIGNAL_BUS.appSetting.langChanged.connect(self.changeLang) # 語言切換

    ##### 功能性函式

    ###### 應用功能

    def selectComicFolder(self, folder: str) -> None:
        """選擇漫畫資料夾

        Args:
            folder (str): 資料夾路徑
        """
        self.view.loading.show() # 顯示處理中
        self.model.appStore.set("comic_folder_path", folder)
        self.view.left_widget.comic_path_button.setText(folder)
        self.view.left_widget.comic_path_button.setToolTip(folder)
        self.model.readComicFolder(folder)
        self.view.loading.close() # 關閉處理中

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
