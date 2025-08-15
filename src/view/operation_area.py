from PySide6.QtWidgets import (
    QWidget, QTabWidget, QPushButton,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
from typing import Any
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.translations import TR
from src.model.main_model import MainModel
## tab
from src.view.tabs.app_info_tab import AppInfoTab
from src.view.tabs.app_setting_tab import AppSettingTab


class OperationArea(QWidget):
    """操作測顯示
    """
    def __init__(self, model: MainModel) -> None:
        """初始化

        Args:
            model (MainModel): 後端
        """
        super().__init__()

        # 初始化 UI
        self.init_ui(model)

        # 訊號連接
        self.signal_connection()

    ##### 初始化函式

    def init_ui(self, model: MainModel) -> None:
        """初始化UI
        
        Args:
            model (MainModel): 後端
        """
        # tab面板
        self.tabs = QTabWidget()
        ## tabs
        ### app設定
        self.app_setting_tab = AppSettingTab(model)
        self.index_app_setting_tab = self.tabs.addTab(self.app_setting_tab, TR.UI_CONSTANTS["設定"]())
        ### app資訊
        self.app_info_tab = AppInfoTab()
        self.index_app_info_tab = self.tabs.addTab(self.app_info_tab, TR.UI_CONSTANTS["關於"]())

        # 執行按鈕
        self.start_button = QPushButton(TR.UI_CONSTANTS["儲存編輯"]())

        # 結構組裝
        self.ui_layout = QVBoxLayout()
        ## 布局設定
        self.ui_layout.setContentsMargins(0, 0, 0 ,0)
        self.ui_layout.setSpacing(4)
        self.ui_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        ## 添加內容
        self.ui_layout.addWidget(self.tabs)
        self.ui_layout.addWidget(self.start_button)
        self.setLayout(self.ui_layout)

    def signal_connection(self):
        """信號連接
        """
        # 語言刷新
        # SIGNAL_BUS.ui.retranslateUi.connect(self.retranslateUi) 

    ##### 功能性函式

    def retranslateUi(self):
        """UI 語言刷新
        """
        # tabs
        ## app設定
        self.tabs.setTabText(self.index_app_setting_tab, TR.UI_CONSTANTS["設定"]())
        self.app_setting_tab.retranslateUi()
        ## app資訊
        self.tabs.setTabText(self.index_app_info_tab, TR.UI_CONSTANTS["關於"]())
        self.app_info_tab.retranslateUi()
        # 啟動按鈕
        self.start_button.setText(TR.UI_CONSTANTS["儲存編輯"]())