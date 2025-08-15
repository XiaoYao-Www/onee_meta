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
    def __init__(self, model: MainModel):
        """初始化

        Args:
            model (MainModel): 後端
        """
        super().__init__()
        # 初始化 UI
        self.init_ui(model)

        # 訊號連接
        self.signal_connection()

        # 功能架構
        self.functional_construction()

    ### 初始化函式 ###

    def init_ui(self, model: MainModel):
        """初始化UI

        Args:
            model (MainModel): 後端
        """
        # 字體大小設定
        font_size_layout = QHBoxLayout()
        self.font_size_label = QLabel(TR.UI_CONSTANTS["字體大小："]())
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 30)
        self.font_size_spin.setValue(model.appSetting.get("font_size", 10)) # 載入初始值

        # 圖片附檔名
        image_extension_layout = QHBoxLayout()
        self.image_extension_label = QLabel(TR.UI_CONSTANTS["圖片附檔名："]())
        self.image_extension_edit = QLineEdit()
        self.image_extension_edit.setText(', '.join(model.appSetting.get("image_exts", []))) # 載入初始值

        # 允許檔案
        allow_files_layout = QHBoxLayout()
        self.allow_files_label = QLabel(TR.UI_CONSTANTS["允許檔案："]())
        self.allow_files_edit = QLineEdit()
        self.allow_files_edit.setText(', '.join(model.appSetting.get("allow_files", []))) # 載入初始值

        # 語言選擇
        lang_select_layout = QHBoxLayout()
        self.lang_select_label = QLabel(TR.UI_CONSTANTS["語言選擇："]())
        self.lang_select_combo = QComboBox()
        keys = [str(key) for key in model.appStore.get("translation_files", {}).keys()]
        keys.insert(0, "")
        self.lang_select_combo.addItems(keys)
        self.lang_select_combo.setCurrentText(model.appSetting.get("lang", "")) # 載入預設值

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
        # 語言刷新
        # SIGNAL_BUS.ui.retranslateUi.connect(self.retranslateUi)
        pass

    def functional_construction(self):
        """功能架構
        """
        pass

    ### 功能函式 ###

    def font_size_changed_display(self, font_size: int) -> None:
        """字體大小變換顯示

        Args:
            font_size (int): 大小
        """
        with QSignalBlocker(self.font_size_spin):
            self.font_size_spin.setValue(font_size)

    def image_extension_changed_display(self, image_exts: list[str]) -> None:
        """圖片附檔名變換顯示

        Args:
            image_exts (list[str]): 副檔名列表
        """
        with QSignalBlocker(self.image_extension_edit):
            self.image_extension_edit.setText(', '.join(image_exts))

    def allow_files_changed_display(self, allow_files: list[str]) -> None:
        """允許檔案變換顯示

        Args:
            allow_files (list[str]): 允許檔案列表
        """
        with QSignalBlocker(self.allow_files_edit):
            self.allow_files_edit.setText(', '.join(allow_files))

    def lang_selected_changed_display(self, selectedLang: str) -> None:
        """語言選擇變換顯示

        Args:
            selectedLang (str): 語言名稱
        """
        with QSignalBlocker(self.lang_select_combo):
            self.lang_select_combo.setCurrentText(selectedLang)

    def retranslateUi(self):
        """語言刷新
        """
        # 字體大小
        self.font_size_label.setText(TR.UI_CONSTANTS["字體大小："]())
        # 圖片附檔名
        self.image_extension_label.setText(TR.UI_CONSTANTS["圖片附檔名："]())
        # 允許檔案
        self.allow_files_label.setText(TR.UI_CONSTANTS["允許檔案："]())
        # 語言選擇
        self.lang_select_label.setText(TR.UI_CONSTANTS["語言選擇："]())