from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QSplitter,
    QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from typing import Optional, Any
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.app_config import appIconPath
from src.view.comic_list_view import ComicListView
from src.view.operation_area import OperationArea
## 翻譯
from src.translations import TR
from src.model.main_model import MainModel

class MainView(QWidget):
    """主窗口
    """
    def __init__(self, model: MainModel):
        """初始化

        Args:
            model (MainModel): 後端
        """
        super().__init__()
        # 初始化 UI
        self.init_ui(model)

        # 應用設定
        self.setWindowTitle(TR.UI_CONSTANTS["Onee Meta"]())
        self.setWindowIcon(QIcon(appIconPath))
        self.resize(900, 750)
        self.change_font_size(model.appSetting.get("font_size", 10))

        # 訊號連接
        self.signal_connection()

        
    ### 初始化函式 ###
    
    def init_ui(self, model: MainModel):
        """UI初始化

        Args:
            model (MainModel): 後端
        """
        # 左右分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        ## 漫畫列表 
        self.left_widget = ComicListView()
        ## 右邊元件
        self.right_widget = OperationArea(model)
        ## 放入 Splitter
        splitter.addWidget(self.left_widget)
        splitter.addWidget(self.right_widget)
        ## 設定初始大小比例 (像素)
        splitter.setSizes([300, 500])

        # 結構組合
        self.ui_layout = QVBoxLayout()
        self.ui_layout.addWidget(splitter)
        self.setLayout(self.ui_layout)

    def signal_connection(self):
        """信號連接
        """
        # 應用設定
        SIGNAL_BUS.appSetting.fontSizeChanged.connect(self.change_font_size)
        # 訊息框
        SIGNAL_BUS.ui.sendCritical.connect(self.send_critical)
        SIGNAL_BUS.ui.sendInformation.connect(self.send_information)
        # 語言刷新
        SIGNAL_BUS.ui.retranslateUi.connect(self.retranslateUi)

    ### 功能性函式 ###

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
        # 漫畫列表
        self.left_widget.retranslateUi()
        # 操作區
        self.right_widget.retranslateUi()