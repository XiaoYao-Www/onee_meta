#####
# 漫畫列表區
#####
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListView,
    QAbstractItemView, QPushButton, QComboBox,
    QLabel, QHBoxLayout, QFileDialog, QSplitter,
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
        self.comic_list.setItemDelegate(NumberedItemDelegate())

        # 第二漫畫列表（雙列表模式用，預設隱藏）
        self.comic_list_2 = QListView()
        self.comic_list_2.setViewMode(QListView.ViewMode.ListMode)
        self.comic_list_2.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.comic_list_2.setDragDropMode(QListView.DragDropMode.InternalMove)
        self.comic_list_2.setDragDropOverwriteMode(False)
        self.comic_list_2.setDragEnabled(True)
        self.comic_list_2.setAcceptDrops(True)
        self.comic_list_2.setDropIndicatorShown(True)
        self.comic_list_2.setItemDelegate(NumberedItemDelegate())
        self.comic_list_2.hide()

        # 雙列表 splitter（先垂直，setDualComicLayout 會依模式切換方向）
        self.list_splitter = QSplitter(Qt.Orientation.Vertical)
        self.list_splitter.addWidget(self.comic_list)
        self.list_splitter.addWidget(self.comic_list_2)

        # 結構組合
        self.ui_layout = QVBoxLayout()
        ## 布局配置 — 留呼吸空間
        self.ui_layout.setContentsMargins(2, 2, 2, 2)
        self.ui_layout.setSpacing(6)
        ## 添加內容
        self.ui_layout.addWidget(self.comic_path_button)
        self.ui_layout.addLayout(info_layout)
        self.ui_layout.addWidget(self.list_splitter, stretch=1)
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

    def comicSelectionChanged(self, from_view: QListView) -> None:
        """漫畫選擇

        Args:
            from_view (QListView): 觸發選擇變更的列表
        """
        # 取得所有選擇
        selected_indexes = from_view.selectedIndexes()
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
        self.comic_list.selectionModel().selectionChanged.connect(
            lambda sel, desel, v=self.comic_list: self.comicSelectionChanged(v)
        )
        self.comic_list_2.setModel(model)
        self.comic_list_2.selectionModel().selectionChanged.connect(
            lambda sel, desel, v=self.comic_list_2: self.comicSelectionChanged(v)
        )

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

    def setDualComicLayout(self, layout: int) -> None:
        """設定雙列表佈局模式

        Args:
            layout: 0=關閉, 1=左右並排, 2=上下垂直
        """
        if layout == 0:
            # 關閉雙列表
            self.comic_list_2.hide()
            self.comic_list.setDragDropMode(QListView.DragDropMode.InternalMove)
        else:
            # 開啟雙列表
            self.comic_list_2.show()
            if layout == 1:
                self.list_splitter.setOrientation(Qt.Orientation.Horizontal)
            else:  # layout == 2
                self.list_splitter.setOrientation(Qt.Orientation.Vertical)
            # 用 setStretchFactor 取代 setSizes：跨 resize 保持比例，不受時機影響
            self.list_splitter.setStretchFactor(0, 1)
            self.list_splitter.setStretchFactor(1, 1)
            self.comic_list.setDragDropMode(QListView.DragDropMode.DragDrop)
            self.comic_list_2.setDragDropMode(QListView.DragDropMode.DragDrop)

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
