from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListView,
    QAbstractItemView, QPushButton, QComboBox,
    QLabel, QHBoxLayout, QFileDialog,
)
from PySide6.QtCore import Qt, QSignalBlocker
from typing import Optional
# 自訂庫
from src.classes.ui.numbered_item_delegate import NumberedItemDelegate
from src.classes.ui.widgets.eliding_button import ElidingButton
from src.translations import TR
from src.signal_bus import SIGNAL_BUS


class ComicListView(QWidget):
    """漫畫列表側顯示
    """
    def __init__(self) -> None:
        super().__init__()
        # 變數初始化
        self.total_comic_count = 0
        self.selected_count = 0
        self.selected_comic_path = False

        # UI 初始化
        self.init_ui()

        # 訊號連結
        self.signal_connection()

    ##### 初始化函式

    def init_ui(self) -> None:
        """UI初始化
        """
        # 路徑選擇按鈕
        self.comic_path_button = ElidingButton(TR.UI_CONSTANTS["選擇漫畫資料夾路徑"](), '', 100)

        # 排序和資訊
        ## 排序
        self.comic_list_sort = QComboBox()
        self.comic_list_sort.addItems([
            TR.UI_CONSTANTS["手動"](),
            TR.UI_CONSTANTS["檔名"](),
        ])
        ## 資訊
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.changeInfoLabel(0)
        ## 組合
        info_layout = QHBoxLayout()
        ### 布局配置
        info_layout.setContentsMargins(0, 0, 0, 0)
        ### 添加內容
        info_layout.addWidget(self.comic_list_sort, stretch= 1)
        info_layout.addWidget(self.info_label, stretch= 7)

        # 漫畫列表
        self.comic_list = QListView()
        # self.comic_list.setModel(self.comic_list_model)
        self.comic_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)  # 多選
        self.comic_list.setDragEnabled(True)           # 可拖曳
        self.comic_list.setAcceptDrops(True)           # 接受拖曳
        self.comic_list.setDropIndicatorShown(True)    # 顯示放置指示
        self.comic_list.setDragDropMode(QListView.DragDropMode.InternalMove)  # 僅允許內部拖曳
        ## 行號
        delegate = NumberedItemDelegate()
        self.comic_list.setItemDelegate(delegate)

        # 結構組合
        self.ui_layout = QVBoxLayout()
        ## 布局配置
        self.ui_layout.setContentsMargins(0, 0, 0, 0)
        self.ui_layout.setSpacing(4)
        ## 添加內容
        self.ui_layout.addWidget(self.comic_path_button)
        self.ui_layout.addLayout(info_layout)
        self.ui_layout.addWidget(self.comic_list)
        self.setLayout(self.ui_layout)

    def signal_connection(self):
        """信號連接
        """
        # 選擇漫畫資料夾
        self.comic_path_button.pressed.connect(self.selectComicFolder)
        # 語言刷新
        # SIGNAL_BUS.ui.retranslateUi.connect(self.retranslateUi)

    ##### 功能性函式

    def selectComicFolder(self) -> None:
        """選擇漫畫路徑
        """
        folder = QFileDialog.getExistingDirectory(self, TR.UI_CONSTANTS["選擇漫畫資料夾"]())
        if folder:
           SIGNAL_BUS.uiSend.selectComicFolder.emit(folder)

    def changeInfoLabel(self, select: Optional[int] = None, total: Optional[int] = None) -> None:
        """切換顯示資訊

        Args:
            select (Optional[int], optional): 設定選中漫畫數. Defaults to None.
            total (Optional[int], optional): 設定總漫畫數. Defaults to None.
        """
        if select != None:
            self.selected_count = select
        if total != None:
            self.total_comic_count = total
        self.info_label.setText(
            TR.UI_CONSTANTS["{selected} / {total} 本漫畫"]().format(
                selected= self.selected_count,
                total= self.total_comic_count,
            )
        )

    def setSortType(self, index: int) -> None:
        """設定排序方式(僅修改顯示)

        Args:
            index (int): 索引
        """
        with(QSignalBlocker(self.comic_list_sort)):
            self.comic_list_sort.setCurrentIndex(index)

    def retranslateUi(self):
        """UI 語言刷新
        """
        # 漫畫資料夾選擇按鈕
        if not self.selected_comic_path:
            self.comic_path_button.setText(TR.UI_CONSTANTS["選擇漫畫資料夾路徑"]())
        # 排序方式選項
        sort_index = self.comic_list_sort.currentIndex()
        self.comic_list_sort.clear()
        self.comic_list_sort.addItems([
            TR.UI_CONSTANTS["手動"](),
            TR.UI_CONSTANTS["檔名"](),
        ])
        self.setSortType(sort_index)
        # 顯示資訊
        self.changeInfoLabel()
