#####
# 主view
#####
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QSplitter,
    QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from typing import Optional, Any
# 自訂庫
from src.signal_bus import SIGNAL_BUS
import src.app_config as APP_CONGIF
from src.view.comic_list_view import ComicListView
from src.view.operation_area import OperationArea
from src.classes.view.widgets.loading_dialog import LoadingDialog
## 翻譯
from src.translations import TR
from src.model.main_model import MainModel

class MainView(QWidget):
    """主窗口
    """
    def __init__(self):
        """初始化
        """
        super().__init__()
        # 初始化 UI
        self.init_ui()

        # 應用設定
        self.setWindowTitle(TR.MAIN_VIEW["Onee Meta"]())
        self.setWindowIcon(QIcon(APP_CONGIF.appIconPath))
        self.resize(900, 750)
        self.changeFontSize(10)

        # 訊號連接
        self.signal_connection()

        
    ### 初始化函式 ###
    
    def init_ui(self):
        """UI初始化
        """
        # 左右分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        ## 漫畫列表 
        self.left_widget = ComicListView()
        ## 右邊元件
        self.right_widget = OperationArea()
        ## 放入 Splitter
        splitter.addWidget(self.left_widget)
        splitter.addWidget(self.right_widget)
        ## 設定初始大小比例 (像素)
        splitter.setSizes([200, 500])

        # 處理中提示
        self.loading = LoadingDialog(TR.MAIN_VIEW["處理中"]())

        # 結構組合
        self.ui_layout = QVBoxLayout()
        self.ui_layout.addWidget(splitter)
        self.setLayout(self.ui_layout)

    def signal_connection(self):
        """信號連接
        """
        # 訊息框
        SIGNAL_BUS.uiRevice.sendCritical.connect(self.sendCritical)
        SIGNAL_BUS.uiRevice.sendInformation.connect(self.sendInformation)
        # 語言刷新
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)

    ### 功能性函式 ###

    ###### 應用設定

    def changeFontSize(self, size: int) -> None:
        """更改字型大小

        Args:
            size (int): 大小
        """
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def retranslateUi(self):
        """UI 語言刷新
        """
        self.setWindowTitle(TR.MAIN_VIEW["Onee Meta"]())
        self.loading.infoLabel.setText(TR.MAIN_VIEW["處理中"]())

    ###### 傳送訊息框

    def sendCritical(self, title: str, text: str) -> None:
        """顯示警告訊息

        Args:
            title (str): 標題
            text (str): 內文
        """
        QMessageBox.critical(self, title, text)

    def sendInformation(self, title: str, text: str) -> None:
        """顯示提示訊息

        Args:
            title (str): 標題
            text (str): 內文
        """
        QMessageBox.information(self, title, text)