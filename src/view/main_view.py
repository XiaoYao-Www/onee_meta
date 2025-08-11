from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox,
)
from PySide6.QtGui import QIcon
from typing import Optional, Any
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.app_config import appIconPath
## 翻譯
from src.translations import TR

class MainView(QWidget):
    """主窗口
    """
    def __init__(self, appSetting: dict[str, Any]):
        """初始化

        Args:
            appSetting (dict[str, Any]): App 設定
        """
        super().__init__()
        # 初始化 UI
        self.init_ui()

        # 應用設定
        self.setWindowTitle(TR.UI_CONSTANTS["Onee Meta"]())
        self.setWindowIcon(QIcon(appIconPath))
        self.resize(900, 750)
        self.change_font_size(appSetting.get("font_size", 10))

        # 訊號連接
        self.signal_connection()

        
    ### 初始化函式 ###
    
    def init_ui(self):
        """ UI初始化 """
        # 結構組合
        self.ui_layout = QVBoxLayout()
        self.setLayout(self.ui_layout)

    def signal_connection(self):
        """ 信號連接 """
        # 應用設定
        SIGNAL_BUS.appSetting.fontSizeChanged.connect(self.change_font_size)
        # 訊息框
        SIGNAL_BUS.ui.sendCritical.connect(self.send_critical)
        SIGNAL_BUS.ui.sendInformation.connect(self.send_information)
        # 語言刷新
        SIGNAL_BUS.ui.retranslateUi.connect(self.retranslateUi)

    ### 功能函式 ###

    def change_font_size(self, size: int) -> None:
        """更改字型大小

        Args:
            size (int): 大小
        """
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def send_critical(self, title: str, text: str) -> None:
        """顯示警告訊息

        Args:
            title (str): 標題
            text (str): 內文
        """
        QMessageBox.critical(self, title, text)

    def send_information(self, title: str, text: str) -> None:
        """顯示提示訊息

        Args:
            title (str): 標題
            text (str): 內文
        """
        QMessageBox.information(self, title, text)

    def retranslateUi(self):
        """UI 語言刷新
        """
        self.setWindowTitle(TR.UI_CONSTANTS["Onee Meta"]())