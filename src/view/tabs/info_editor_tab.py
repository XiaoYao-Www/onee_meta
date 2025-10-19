#####
# 資訊編輯頁面
#####
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog, QLineEdit,
    QMessageBox, QComboBox, QAbstractItemView, QTabWidget,
    QTextEdit, QProgressBar, QSpinBox, QScrollArea, QSizePolicy,
    QToolButton
)
from PySide6.QtCore import Qt
from typing import Dict, List
# 自訂庫
from src.signal_bus import SIGNAL_BUS
import src.app_config as APP_CONFIG
from src.classes.view.widgets.smart_integer_field import SmartIntegerField
from src.classes.model.comic_data import ComicData, XmlComicInfo
## 翻譯
from src.translations import TR

class InfoEditorTab(QWidget):
    def __init__(self):
        super().__init__()
        # 變數創建
        self.updating_fields = False
        self.toggle_buttons = {}
        self.editors: Dict[str, QLineEdit | SmartIntegerField | QTextEdit | QComboBox] = {}
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

        # 動態創建UI
        for section_key, fields in APP_CONFIG.infoEditorTabConfig.items():
            toggle_button = QToolButton(text=TR.INFO_EDITOR_TAB[section_key](), checkable=True, checked=False) # type: ignore[attr-defined]
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
                label = QLabel(TR.INFO_EDITOR_TAB[field_cfg["label"]]())
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                hlayout.addWidget(label, stretch=1)
                self.labels[field_cfg["info_key"]] = label

                widget_cls = field_cfg["type"]
                if widget_cls == QComboBox:
                    widget = QComboBox()
                    widget.addItems(field_cfg.get("options", ["{keep}"]))
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
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)

    def functional_construction(self):
        """ 功能建構 """
        pass

    ### 功能函式 ###

    def setComicInfoData(self, comicData: List[XmlComicInfo]) -> None:
        """多筆資料設定：若欄位值一致就顯示該值，否則顯示 {keep}

        Args:
            comicData (List[XmlComicInfo]): 漫畫資料數據列表
        """
        self.updating_fields = True
        try:
            for section, fields in APP_CONFIG.infoEditorTabConfig.items():
                for field_key, field_cfg in fields.items():
                    info_key = field_cfg["info_key"]
                    values = []

                    for d in comicData:
                        # 每筆資料從 fields 中抓取對應欄位
                        val = d.get("fields", {}).get("base", {}).get(info_key, "") # 目前只有 base
                        values.append(val)

                    if not values:
                        display_val = ""
                    elif all(v == values[0] for v in values):
                        display_val = values[0]
                    else:
                        display_val = "{keep}"

                    editor = self.editors.get(info_key)
                    if isinstance(editor, QComboBox):
                        idx = editor.findText(display_val)
                        if idx == -1 or idx == None:
                            idx = editor.findText("{keep}")
                        editor.setCurrentIndex(idx)
                    elif isinstance(editor, QTextEdit):
                        editor.setPlainText(display_val)
                    elif isinstance(editor, SmartIntegerField):
                        if display_val == "{keep}" or display_val == "" or display_val == "-1":
                            editor.setValue(display_val)
                        else:
                            try:
                                editor.setValue(int(display_val))
                            except ValueError:
                                editor.setValue("{keep}")
                    elif editor != None:
                        editor.setText(display_val)
        finally:
            self.updating_fields = False

    def getComicInfoData(self) -> XmlComicInfo:
        """取得目前編輯器中的值
            不回傳鍵 => keep
            回傳 "" => clear
            回傳值 => value

        Returns:
            XmlComicInfo: 漫畫資料數據
        """
        result: XmlComicInfo = {
            "nsmap": {},
            "fields": {
                "base": {}
            }
        }
        for section, fields in APP_CONFIG.infoEditorTabConfig.items():
            for field_key, field_cfg in fields.items():
                info_key = field_cfg["info_key"]
                editor = self.editors.get(info_key)
                if isinstance(editor, QComboBox):
                    val = editor.currentText()
                    if val == "{keep}":
                        continue
                elif isinstance(editor, QTextEdit):
                    val = editor.toPlainText()
                    if val == "{keep}":
                        continue
                elif isinstance(editor, SmartIntegerField):
                    state = editor.get_state()
                    if state == "preserve":
                        continue
                    elif state == "clear":
                        val = ""
                    else:
                        val = str(editor.value())
                elif isinstance(editor, QLineEdit):
                    val = editor.text()
                    if val == "{keep}":
                        continue
                else:
                    continue
                result["fields"]["base"][info_key] = val
        return result


    ### UI介面 ###

    def retranslateUi(self):
        """ UI 語言刷新 """
        for section_key, fields in APP_CONFIG.infoEditorTabConfig.items():
            toggle_button: QToolButton = self.toggle_buttons[section_key]
            toggle_button.setText(TR.INFO_EDITOR_TAB[section_key]())

            for field_key, field_cfg in fields.items():
                label: QLabel = self.labels[field_cfg["info_key"]]
                label.setText(TR.INFO_EDITOR_TAB[field_cfg["label"]]())
