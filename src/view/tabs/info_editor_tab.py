from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog, QLineEdit,
    QMessageBox, QComboBox, QAbstractItemView, QTabWidget,
    QTextEdit, QProgressBar, QSpinBox, QScrollArea, QSizePolicy,
    QToolButton
)
from PySide6.QtCore import Qt
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.app_config import infoEditorTabConfig
from src.classes.ui.widgets.smart_integer_field import SmartIntegerField
## 翻譯
from src.translations import TR

class InfoEditorTab(QWidget):
    def __init__(self):
        super().__init__()
        # 變數創建
        self.toggle_buttons = {}
        self.editors = {}
        self.labels = {}

        # 初始化 UI
        self.init_ui()

        # 訊號連接
        self.signal_connection()

        # 功能建構
        self.functional_construction()

    ### 初始化函式 ### 

    def init_ui(self):
        """ 初始化UI元件 """
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for section_key, fields in infoEditorTabConfig.items():
            toggle_button = QToolButton(text=TR.INFO_EDITOR_TAB_CONFIG[section_key](), checkable=True, checked=False) # type: ignore[attr-defined]
            toggle_button.setStyleSheet("QToolButton { border: none; }")
            toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            toggle_button.setArrowType(Qt.ArrowType.RightArrow)
            self.toggle_buttons[section_key] = toggle_button

            content_area = QWidget()
            content_layout = QVBoxLayout()
            content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            content_area.setLayout(content_layout)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(content_area)
            scroll.setVisible(False)

            def make_toggle_func(button=toggle_button, area=scroll):
                return lambda checked: (button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow), area.setVisible(checked))

            toggle_button.toggled.connect(make_toggle_func())

            layout.addWidget(toggle_button)
            layout.addWidget(scroll)

            for field_key, field_cfg in fields.items():
                hlayout = QHBoxLayout()
                label = QLabel(TR.INFO_EDITOR_TAB_CONFIG[field_cfg["label"]]())
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                hlayout.addWidget(label, stretch=1)
                self.labels[field_cfg["info_key"]] = label

                widget_cls = field_cfg["type"]
                if widget_cls == QComboBox:
                    widget = QComboBox()
                    widget.addItems(field_cfg.get("options", ["{保留}"]))
                elif widget_cls == SmartIntegerField:
                    widget = SmartIntegerField()
                elif widget_cls == QTextEdit:
                    widget = QTextEdit()
                else:
                    widget = widget_cls()

                hlayout.addWidget(widget, stretch=7)
                content_layout.addLayout(hlayout)
                self.editors[field_cfg["info_key"]] = widget

        # 加入主 Layout
        self.setLayout(layout)

    def signal_connection(self):
        """ 訊號連結 """
        pass
        # 語言刷新
        # SIGNAL_BUS.ui.retranslateUi.connect(self.retranslateUi)

    def functional_construction(self):
        """ 功能建構 """
        pass

    ### 功能函式 ###

    def retranslateUi(self):
        """ UI 語言刷新 """
        for section_key, fields in infoEditorTabConfig.items():
            toggle_button: QToolButton = self.toggle_buttons[section_key]
            toggle_button.setText(TR.INFO_EDITOR_TAB_CONFIG[section_key]())

            for field_key, field_cfg in fields.items():
                label: QLabel = self.labels[field_cfg["info_key"]]
                label.setText(TR.INFO_EDITOR_TAB_CONFIG[field_cfg["label"]]())
