from PySide6.QtCore import QObject, QTranslator
from PySide6.QtWidgets import QApplication
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
        # App設定
        SIGNAL_BUS.appSetting.langChanged.connect(self.changeLang) # 語言切換

    ##### 功能性函式

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
