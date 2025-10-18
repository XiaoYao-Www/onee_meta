#####
# 應用操作區
#####
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QPushButton,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
from typing import Any, Optional
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.translations import TR
from src.model.main_model import MainModel
# tab
from src.view.tabs.app_info_tab import AppInfoTab
from src.view.tabs.app_setting_tab import AppSettingTab
from src.view.tabs.info_editor_tab import InfoEditorTab


class OperationArea(QWidget):
    """操作測顯示
    """
    def __init__(self) -> None:
        """初始化

        Args:
            model (MainModel): 後端
        """
        super().__init__()

        # 初始化 UI
        self.init_ui()

        # 訊號連接
        self.signal_connection()

    ##### 初始化函式

    def init_ui(self) -> None:
        """初始化UI
        
        Args:
            model (MainModel): 後端
        """
        # tab面板
        self.tabs = QTabWidget()
        ## tabs
        ### 資訊編輯頁
        self.info_editor_tab = InfoEditorTab()
        self.index_info_editor_tab = self.tabs.addTab(self.info_editor_tab, TR.OPERATION_AREA["資訊"]())
        ### app設定
        self.app_setting_tab = AppSettingTab()
        self.index_app_setting_tab = self.tabs.addTab(self.app_setting_tab, TR.OPERATION_AREA["設定"]())
        ### app資訊
        self.app_info_tab = AppInfoTab()
        self.index_app_info_tab = self.tabs.addTab(self.app_info_tab, TR.OPERATION_AREA["關於"]())

        # 執行按鈕
        self.start_button = QPushButton(TR.OPERATION_AREA["儲存編輯"]())

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
        ## 預設顯示配置
        self.tabs.setTabVisible(self.index_info_editor_tab, False)
        self.tabs.setCurrentIndex(self.index_app_info_tab)
        self.changeStartButtonVisible(False)

    def signal_connection(self):
        """信號連接
        """
        # 切換開始按鈕顯示狀態
        self.tabs.currentChanged.connect(lambda _: self.changeStartButtonVisible())
        # 開始按鈕
        self.start_button.clicked.connect(lambda _: SIGNAL_BUS.uiSend.startProcess.emit())
        # 語言刷新
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi) 

    ##### 功能性函式

    def changeStartButtonVisible(self, state: Optional[bool] = None) -> None:
        """設置開始按鈕可見狀態
        """
        if state != None:
            self.start_button.setVisible(state)
        else:
            self.start_button.setVisible(
                not(self.tabs.currentIndex() in [self.index_app_info_tab, self.index_app_setting_tab])
            )


    def retranslateUi(self):
        """UI 語言刷新
        """
        # 分頁標題
        ## 資訊編輯
        self.tabs.setTabText(self.index_info_editor_tab, TR.OPERATION_AREA["資訊"]())
        ## app設定
        self.tabs.setTabText(self.index_app_setting_tab, TR.OPERATION_AREA["設定"]())
        ## app資訊
        self.tabs.setTabText(self.index_app_info_tab, TR.OPERATION_AREA["關於"]())
        # 啟動按鈕
        self.start_button.setText(TR.OPERATION_AREA["儲存編輯"]())