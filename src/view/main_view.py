#####
# 主view
#####
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QSplitter,
    QTextEdit, QLabel, QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from typing import Optional, Any
# 自訂庫
from src.signal_bus import SIGNAL_BUS
import src.app_config as APP_CONGIF
from src.layout_constants import WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_FONT_SIZE, MAIN_SPLITTER_SIZES
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
        super().__init__()

        # 狀態列文字
        self._status_text = "就緒"

        self.init_ui()

        self.setWindowTitle(TR.MAIN_VIEW["Onee Meta"]())
        self.setWindowIcon(QIcon(APP_CONGIF.appIconPath))
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.changeFontSize(DEFAULT_FONT_SIZE)

        self.signal_connection()

    ### 初始化 ###

    def init_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_widget = ComicListView()
        self.right_widget = OperationArea()
        splitter.addWidget(self.left_widget)
        splitter.addWidget(self.right_widget)
        splitter.setSizes(list(MAIN_SPLITTER_SIZES))

        self.loading = LoadingDialog(TR.MAIN_VIEW["處理中"]())

        # 狀態列
        self.status_bar = QLabel(self._status_text)
        self.status_bar.setObjectName("statusBar")
        self.status_bar.setStyleSheet("""
            QLabel#statusBar {
                background: #181825;
                border-top: 1px solid #45475a;
                padding: 4px 12px;
                color: #a6adc8;
                font-size: 12px;
            }
        """)
        self.status_bar.setFixedHeight(28)

        # 主佈局
        self.ui_layout = QVBoxLayout()
        self.ui_layout.setContentsMargins(8, 8, 8, 0)  # 左右上留8px呼吸空間
        self.ui_layout.setSpacing(6)
        self.ui_layout.addWidget(splitter)
        self.ui_layout.addWidget(self.status_bar)
        self.setLayout(self.ui_layout)

    def signal_connection(self):
        SIGNAL_BUS.uiRevice.sendCritical.connect(self.sendCritical)
        SIGNAL_BUS.uiRevice.sendInformation.connect(self.sendInformation)
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)

    ### 功能 ###

    def setStatus(self, text: str) -> None:
        """設定狀態列文字"""
        self._status_text = text
        self.status_bar.setText(text)

    def changeFontSize(self, size: int) -> None:
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def retranslateUi(self):
        self.setWindowTitle(TR.MAIN_VIEW["Onee Meta"]())
        self.loading.infoLabel.setText(TR.MAIN_VIEW["處理中"]())

    def sendCritical(self, title: str, text: str) -> None:
        QMessageBox.critical(self, title, text)

    def sendInformation(self, title: str, text: str) -> None:
        QMessageBox.information(self, title, text)
