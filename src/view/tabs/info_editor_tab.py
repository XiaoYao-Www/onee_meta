#####
# 資訊編輯頁面
#####
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog, QLineEdit,
    QMessageBox, QComboBox, QAbstractItemView, QTabWidget,
    QTextEdit, QProgressBar, QSpinBox, QScrollArea, QSizePolicy,
    QToolButton, QFrame, QSplitter, QGridLayout,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from typing import Dict, List, cast
import re
# 自訂庫
from src.classes.calibre_scanner import CalibreSidecar
from src.signal_bus import SIGNAL_BUS
import src.app_config as APP_CONFIG
from src.classes.view.widgets.smart_integer_field import SmartIntegerField
from src.classes.view.widgets.aspect_ratio_label import AspectRatioLabel
from src.classes.model.comic_data import ComicData, XmlComicInfo
from src.classes.controller.comic_placeholder_data import ComicPlaceholderData
from src.classes.view.widgets.data_card import DataCard
## 翻譯
from src.translations import TR


class InfoEditorTab(QWidget):
    def __init__(self):
        super().__init__()
        # 變數創建
        self.updating_fields = False
        self.toggle_buttons = {}
        self.editors: Dict[str, QLineEdit | SmartIntegerField | QTextEdit | QComboBox] = {}
        self.labels: Dict[str,QLabel] = {}

        # --- 新增側邊欄控制變數 ---
        self.SIDEBAR_WIDTH = 250
        self.is_sidebar_expanded = False # 預設縮起

        # 初始化 UI
        self.init_ui()

        # 訊號連接
        self.signal_connection()

        # 功能建構
        self.functional_construction()

    ### 初始化函式 ### 

    def init_ui(self):
        """ 初始化UI元件 """
        # 主布局
        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # 拖動桿
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 漫畫資料編輯區
        self.info_edit_widget = QWidget()
        info_edit_layout = QVBoxLayout(self.info_edit_widget)
        info_edit_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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

            info_edit_layout.addWidget(toggle_button)
            info_edit_layout.addWidget(scroll)

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
    
        # 4. 右側側邊欄
        # 建立 Splitter 設為垂直方向
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        # 上方元件
        self.image_label = AspectRatioLabel("圖片載入中...")
        self.right_splitter.addWidget(self.image_label)

        # 下方元件
        self.info_scanner_container = QWidget()
        self.info_scanner_layout = QVBoxLayout(self.info_scanner_container)
        self.info_scanner_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        ##### 右側資訊抓取 #####

        ##### 搜尋區
        self.info_scanner_search = QGridLayout()
        self.info_scanner_search.setContentsMargins(0, 0, 0, 0)
        self.info_scanner_search.setSpacing(0)
        self.info_scanner_search.addWidget(QLabel("書名"), 0, 0)
        self.info_scanner_search_bookname = QLineEdit()
        self.info_scanner_search.addWidget(self.info_scanner_search_bookname, 0, 1)
        self.info_scanner_search.addWidget(QLabel("作者"), 1, 0)
        self.info_scanner_search_author = QLineEdit()
        self.info_scanner_search.addWidget(self.info_scanner_search_author, 1, 1)
        self.info_scanner_search.addWidget(QLabel("ISBN"), 3, 0)
        self.info_scanner_search_isbn = QLineEdit()
        self.info_scanner_search.addWidget(self.info_scanner_search_isbn, 3, 1)
        self.info_scanner_search_button = QPushButton("搜尋")
        self.info_scanner_search.addWidget(self.info_scanner_search_button, 4, 0, 1, 2)

        ##### 列表區

        self.info_scanner_scroll_area = QScrollArea()
        self.info_scanner_scroll_area.setWidgetResizable(True)
        self.info_scanner_scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.info_scanner_scroll_content = QWidget()
        self.info_scanner_scroll_content_layout = QVBoxLayout(self.info_scanner_scroll_content)
        self.info_scanner_scroll_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.info_scanner_scroll_area.setWidget(self.info_scanner_scroll_content)


        self.info_scanner_layout.addLayout(self.info_scanner_search)
        self.info_scanner_layout.addWidget(self.info_scanner_scroll_area)

        #######################

        self.right_splitter.addWidget(self.info_scanner_container)

        # 設定初始比例 (例如 7:3)
        self.right_splitter.setStretchFactor(0, 7)
        self.right_splitter.setStretchFactor(1, 3)

        # 最後將 Splitter 加入右側主佈局
        self.right_sidebar_layout = QVBoxLayout()
        self.right_sidebar_layout.addWidget(self.right_splitter)

        self.right_sidebar_widget = QWidget()
        self.right_sidebar_widget.setLayout(self.right_sidebar_layout)
        
        # 5. 將元件加入 Splitter
        self.splitter.addWidget(self.info_edit_widget)
        self.splitter.addWidget(self.right_sidebar_widget)

        # 6. 設定初始比例 (左側佔滿，右側 0)
        self.splitter.setSizes([900, 100]) 
        self.splitter.setStretchFactor(0, 1) # 左側優先吃掉空間
        self.splitter.setStretchFactor(1, 0)

        # 組合到主佈局
        self.main_h_layout.addWidget(self.splitter)

    def signal_connection(self):
        """ 訊號連結 """
        self.info_scanner_search_button.clicked.connect(
            lambda: SIGNAL_BUS.uiSend.runScanner.emit(
                self.info_scanner_search_bookname.text(),
                self.info_scanner_search_author.text(), 
                self.info_scanner_search_isbn.text()
            )
        )

        # 語言刷新
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)

    def functional_construction(self):
        """ 功能建構 """
        pass

    ### 功能函式 ###

    def resolve_card_element_clicked(self, filed_name: str, text_value: str):
        """ 解析卡片元素被點擊時的資訊 """
        if filed_name == "Title":
            cast(QLineEdit, self.editors["Title"]).setText(text_value)
        elif filed_name == "Author(s)":
            cast(QLineEdit, self.editors["Writer"]).setText(text_value)
        elif filed_name == "Publisher":
            cast(QLineEdit, self.editors["Publisher"]).setText(text_value)
        elif filed_name == "Languages":
            cast(QLineEdit, self.editors["Language"]).setText(text_value)
        elif filed_name == "Identifiers":
            cast(QLineEdit, self.editors["Notes"]).setText(text_value)
        elif filed_name == "Tag":
            tags_list = [t.strip() for t in text_value.split(',')]
            for tag in tags_list:
                now_tags = cast(QLineEdit, self.editors["Tags"]).text()
                if now_tags == "":
                    cast(QLineEdit, self.editors["Tags"]).setText(tag)
                elif not(tag in now_tags):
                    cast(QLineEdit, self.editors["Tags"]).setText(now_tags + "," + tag)


    def clear_data_cards(self):
        """ 清空目前列表中的所有資料卡片 """
        # 反向迴圈刪除 Layout 中的 Widget
        while self.info_scanner_scroll_content_layout.count():
            item = self.info_scanner_scroll_content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_data_cards(self, data_list):
        """ 刷新函數：清空舊資料並載入新資料 """
        self.clear_data_cards()
        
        # 逐筆建立資料卡片並加入佈局
        for item in data_list:
            card = DataCard(item)
            card.element_clicked.connect(self.resolve_card_element_clicked)
            self.info_scanner_scroll_content_layout.addWidget(card)

    def setComicInfoData(self, comicData: List[ComicData]) -> None:
        """多筆資料設定：若欄位值一致就顯示該值，否則顯示 {keep}

        Args:
            comicData (List[ComicInfo]): 漫畫資料列表
        """
        self.updating_fields = True
        try:
            if len(comicData) > 1:
                self.right_sidebar_widget.setVisible(False)
            else:
                self.right_sidebar_widget.setVisible(True)
                self.info_scanner_search_bookname.setText(comicData[0]["comic_path"])
                self.clear_data_cards()

            # 更新資料欄位
            for section, fields in APP_CONFIG.infoEditorTabConfig.items():
                for field_key, field_cfg in fields.items():
                    info_key = field_cfg["info_key"]
                    values = []

                    for d in comicData:
                        # 每筆資料從 fields 中抓取對應欄位
                        val = d.get("xml_comic_info").get("fields", {}).get("base", {}).get(info_key, "") # 目前只有 base
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
                        if display_val == "{keep}" or display_val == "":
                            editor.setValue(display_val)
                        else:
                            try:
                                editor.setValue(int(display_val))
                            except ValueError:
                                editor.setValue("{keep}")
                    elif editor != None:
                        editor.setText(display_val)
            
            # 更新圖片
            if len(comicData) > 1:
                self.image_label.setText("多本漫畫無法顯示圖片")
            elif not(comicData[0].get("first_image") is None):
                self.image_label.setPixmap(cast(QPixmap, comicData[0].get("first_image")))
            else:
                self.image_label.setText("無法顯示圖片")

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
        valid_keys = set(ComicPlaceholderData.__annotations__.keys())
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
                    val = editor.value()
                    if val == "{keep}":
                        continue
                    elif val.startswith("{"):
                        match = re.fullmatch(r"\{(\w*)\}", val)
                        if not match or match.group(1) not in valid_keys:
                            continue
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
