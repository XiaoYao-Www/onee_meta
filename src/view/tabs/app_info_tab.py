#####
# 應用資訊分頁
#####
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QTextEdit,
)
# 自訂庫
from src.classes.view.widgets.clickable_url_label import ClickableUrlLabel
import src.app_config as APP_CONFIG
from src.signal_bus import SIGNAL_BUS
## 翻譯
from src.translations import TR


class AppInfoTab(QWidget):
    """應用關於頁
    """
    def __init__(self):
        super().__init__()
        # 初始化 UI
        self.init_ui()

        # 訊號連接
        self.signal_connection()

    ### 初始化函式 ###

    def init_ui(self):
        """初始化UI元件
        """
        # 作者資訊
        ## 標籤
        self.about_author_label = QLabel(TR.APP_INFO_TAB["👻 作者資訊"]())
        self.about_author_label.setStyleSheet("font-size: 23px; font-weight: bold;")
        ## 介紹內容
        self.about_author_text = QTextEdit()
        self.about_author_text.setPlainText(TR.APP_INFO_TAB["自我介紹"]())
        self.about_author_text.setReadOnly(True)
        ## github 連結
        self.about_author_github_label = ClickableUrlLabel(TR.APP_INFO_TAB["作者 Github 連結"](), "https://github.com/XiaoYao-Www")

        # 軟體資訊
        ## 標籤
        self.about_software_label = QLabel(TR.APP_INFO_TAB["📦 軟體資訊"]())
        self.about_software_label.setStyleSheet("font-size: 23px; font-weight: bold;")
        ## 介紹內容
        self.about_software_text = QTextEdit()
        self.about_software_text.setPlainText(
            TR.APP_INFO_TAB["軟體介紹"]().format(version = APP_CONFIG.appVersion)
        )
        self.about_software_text.setReadOnly(True)
        ## github 連結
        self.about_software_github_label = ClickableUrlLabel(TR.APP_INFO_TAB["專案 GitHub 專案連結"](), "https://github.com/XiaoYao-Www/onee_meta")

        # 結構組合
        ui_layout = QVBoxLayout()
        ui_layout.addWidget(self.about_author_label)
        ui_layout.addWidget(self.about_author_text)
        ui_layout.addWidget(self.about_author_github_label)
        ui_layout.addWidget(self.about_software_label)
        ui_layout.addWidget(self.about_software_text)
        ui_layout.addWidget(self.about_software_github_label)
        self.setLayout(ui_layout)

    def signal_connection(self):
        """ 訊號連接 """
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)
        pass

    ### 功能函式 ###

    def retranslateUi(self):
        """ UI 語言刷新 """
        self.about_author_label.setText(TR.APP_INFO_TAB["👻 作者資訊"]())
        self.about_author_text.setPlainText(TR.APP_INFO_TAB["自我介紹"]())
        self.about_author_github_label.setText(TR.APP_INFO_TAB["作者 Github 連結"]())
        #
        self.about_software_label.setText(TR.APP_INFO_TAB["📦 軟體資訊"]())
        self.about_software_text.setPlainText(
            TR.APP_INFO_TAB["軟體介紹"]().format(version = APP_CONFIG.appVersion)
        )
        self.about_software_github_label.setText(TR.APP_INFO_TAB["專案 GitHub 專案連結"]())
