#####
# 漫畫列表區
#####
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListView,
    QAbstractItemView, QPushButton, QComboBox,
    QLabel, QHBoxLayout, QFileDialog,
)
from PySide6.QtCore import Qt, QSignalBlocker, QAbstractItemModel, QItemSelection
from typing import Optional, Dict, List, Set
# 自訂庫
from src.classes.view.widgets.numbered_item_delegate import NumberedItemDelegate
from src.classes.view.widgets.eliding_button import ElidingButton
# from src.classes.ui.widgets.custom_comic_list import CustomComicList
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
        self.comic_path_button = ElidingButton(TR.COMIC_LIST_VIEW["選擇漫畫資料夾路徑"](), '', 100)

        # 排序和資訊
        ## 排序
        self.comic_list_sort = QComboBox()
        self.comic_list_sort.addItems([
            TR.COMIC_LIST_VIEW["手動"](),
            TR.COMIC_LIST_VIEW["檔名"](),
            TR.COMIC_LIST_VIEW["集數"](),
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
        ## 設定
        self.comic_list.setViewMode(QListView.ViewMode.ListMode) # 列表模式
        self.comic_list.setSelectionMode(QListView.SelectionMode.ExtendedSelection)  # 支援多選
        self.comic_list.setDragDropMode(QListView.DragDropMode.InternalMove) # 列表內拖曳
        self.comic_list.setDragDropOverwriteMode(False)  # 禁用覆蓋模式，啟用插入指示器
        self.comic_list.setDragEnabled(True) # 可拖曳
        self.comic_list.setAcceptDrops(True) # 可放置
        self.comic_list.setDropIndicatorShown(True)  # 顯示 drop 指示線
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
        # 漫畫列表排序改變
        self.comic_list_sort.currentIndexChanged.connect(
            lambda x: SIGNAL_BUS.uiSend.comicListSort.emit(x)
        )
        # 漫畫選擇
        # -> 寫在模型設定裡
        # 語言刷新
        SIGNAL_BUS.uiRevice.translateUi.connect(self.retranslateUi)

    ### 功能性函式 ###

    ###### 介面功能

    def selectComicFolder(self) -> None:
        """選擇漫畫路徑
        """
        folder = QFileDialog.getExistingDirectory(self, TR.COMIC_LIST_VIEW["選擇漫畫資料夾"]())
        if folder:
           SIGNAL_BUS.uiSend.selectComicFolder.emit(folder)

    def comicSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        """漫畫選擇

        Args:
            selected (QItemSelection): 選擇項
            deselected (QItemSelection): 未選擇項
        """
        # 取得所有選擇
        selection_model = self.comic_list.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        # 取得row列表
        selected_rows = sorted({idx.row() for idx in selected_indexes})
        # 傳送和修改顯示
        SIGNAL_BUS.uiSend.comicListSelected.emit(selected_rows)
        self.changeInfoLabel(select=len(selected_rows))

    ###### 介面設定

    def setListModel(self, model: QAbstractItemModel) -> None:
        """設定列表模型

        Args:
            model (QAbstractItemModel): 模型
        """
        self.comic_list.setModel(model)
        self.comic_list.selectionModel().selectionChanged.connect(self.comicSelectionChanged)

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
            TR.COMIC_LIST_VIEW["{selected} / {total} 本漫畫"]().format(
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
            self.comic_path_button.setText(TR.COMIC_LIST_VIEW["選擇漫畫資料夾路徑"]())
        # 排序方式選項
        sort_index = self.comic_list_sort.currentIndex()
        self.comic_list_sort.clear()
        self.comic_list_sort.addItems([
            TR.COMIC_LIST_VIEW["手動"](),
            TR.COMIC_LIST_VIEW["檔名"](),
            TR.COMIC_LIST_VIEW["集數"](),
        ])
        self.setSortType(sort_index)
        # 顯示資訊
        self.changeInfoLabel()
