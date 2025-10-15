#####
# 設定分頁
#####
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, QSignalBlocker
from typing import Any
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.model.main_model import MainModel
## 翻譯
from src.translations import TR

class AppSettingTab(QWidget):
    def __init__(self):
        """初始化

        Args:
            model (MainModel): 後端
        """
        super().__init__()
        # 初始化 UI
        self.init_ui()

        # 訊號連接
        self.signal_connection()

        # 功能架構
        self.functional_construction()

    ### 初始化函式 ###

    def init_ui(self):
        """初始化UI

        Args:
            model (MainModel): 後端
        """
        # 字體大小設定
        font_size_layout = QHBoxLayout()
        self.font_size_label = QLabel(TR.APP_SETTING_TAB["字體大小："]())
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 30)

        # 圖片附檔名
        image_extension_layout = QHBoxLayout()
        self.image_extension_label = QLabel(TR.APP_SETTING_TAB["圖片附檔名："]())
        self.image_extension_edit = QLineEdit()

        # 允許檔案
        allow_files_layout = QHBoxLayout()
        self.allow_files_label = QLabel(TR.APP_SETTING_TAB["允許檔案："]())
        self.allow_files_edit = QLineEdit()

        # 語言選擇
        lang_select_layout = QHBoxLayout()
        self.lang_select_label = QLabel(TR.APP_SETTING_TAB["語言選擇："]())
        self.lang_select_combo = QComboBox()

        # 結構組合
        ui_layout = QVBoxLayout()
        ## 布局設置
        ui_layout.setSpacing(4)
        ui_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ## 設置內容
        ### 字體大小
        font_size_layout.addWidget(self.font_size_label, stretch=1)
        font_size_layout.addWidget(self.font_size_spin, stretch=4)
        ui_layout.addLayout(font_size_layout)
        ### 圖片附檔名
        image_extension_layout.addWidget(self.image_extension_label, stretch=1)
        image_extension_layout.addWidget(self.image_extension_edit, stretch=4)
        ui_layout.addLayout(image_extension_layout)
        ### 允許檔案
        allow_files_layout.addWidget(self.allow_files_label, stretch=1)
        allow_files_layout.addWidget(self.allow_files_edit, stretch=4)
        ui_layout.addLayout(allow_files_layout)
        ### 選擇語言
        lang_select_layout.addWidget(self.lang_select_label, stretch=1)
        lang_select_layout.addWidget(self.lang_select_combo, stretch=4)
        ui_layout.addLayout(lang_select_layout)
        ### 主要輸出
        self.setLayout(ui_layout)

    def signal_connection(self):
        """訊號連接
        """
        # 字體大小設定
        self.font_size_spin.valueChanged.connect(lambda size: SIGNAL_BUS.uiSend.fontSizeSet.emit(size))
        # 圖片副檔名設定
        self.image_extension_edit.textChanged.connect(self.settingImageExtension)
        # 允許檔案設定
        self.allow_files_edit.textChanged.connect(self.settingAllowFile)
        # 修改語言
        self.lang_select_combo.currentTextChanged.connect(lambda lang: SIGNAL_BUS.uiSend.langChange.emit(lang))
        # 語言刷新
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)

    def functional_construction(self):
        """功能架構
        """
        pass

    ### 功能函式 ###

    ###### UI 改變

    def fontSizeChangedDisplay(self, font_size: int) -> None:
        """字體大小變換顯示

        Args:
            font_size (int): 大小
        """
        with QSignalBlocker(self.font_size_spin):
            self.font_size_spin.setValue(font_size)

    def imageExtensionChangedDisplay(self, image_exts: list[str]) -> None:
        """圖片附檔名變換顯示

        Args:
            image_exts (list[str]): 副檔名列表
        """
        with QSignalBlocker(self.image_extension_edit):
            self.image_extension_edit.setText(', '.join(image_exts))

    def allowFilesChangedDisplay(self, allow_files: list[str]) -> None:
        """允許檔案變換顯示

        Args:
            allow_files (list[str]): 允許檔案列表
        """
        with QSignalBlocker(self.allow_files_edit):
            self.allow_files_edit.setText(', '.join(allow_files))

    def langSelectedChangedDisplay(self, selectedLang: str) -> None:
        """語言選擇變換顯示

        Args:
            selectedLang (str): 語言名稱
        """
        with QSignalBlocker(self.lang_select_combo):
            self.lang_select_combo.setCurrentText(selectedLang)

    ###### 設定修改

    def settingImageExtension(self, extStr: str) -> None:
        """修改圖片副檔名設定

        Args:
            extStr (str): 副檔名字串
        """
        ext_list = [item.strip() for item in extStr.split(',')]
        SIGNAL_BUS.uiSend.imgExtensionSet.emit(ext_list)

    def settingAllowFile(self, fileStr: str) -> None:
        """修改允許檔案

        Args:
            fileStr (str): 允許檔案字串
        """
        file_list = [item.strip() for item in fileStr.split(',')]
        SIGNAL_BUS.uiSend.allowFileSet.emit(file_list)

    ###### 其它

    def retranslateUi(self):
        """語言刷新
        """
        # 字體大小
        self.font_size_label.setText(TR.APP_SETTING_TAB["字體大小："]())
        # 圖片附檔名
        self.image_extension_label.setText(TR.APP_SETTING_TAB["圖片附檔名："]())
        # 允許檔案
        self.allow_files_label.setText(TR.APP_SETTING_TAB["允許檔案："]())
        # 語言選擇
        self.lang_select_label.setText(TR.APP_SETTING_TAB["語言選擇："]())