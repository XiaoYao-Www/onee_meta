from typing import List, Dict
from PySide6.QtCore import Qt, QModelIndex, Signal, QStringListModel
from PySide6.QtWidgets import QListView, QAbstractItemView
from PySide6.QtGui import QDropEvent


class CustomComicList(QListView):
    """自訂漫畫顯示 ListView
    """

    selectionChangedSignal = Signal(dict)

    def __init__(self, items: List[str] = []):
        super().__init__()

        # 指定模型
        self.comic_list_model = QStringListModel(items)
        self.setModel(self.comic_list_model)

        # 列表功能設定
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)  # 多選
        self.setDragEnabled(True)  # 可拖曳
        self.setAcceptDrops(True)  # 接受拖曳
        self.setDropIndicatorShown(True)  # 顯示放置指示
        self.setDragDropMode(QListView.DragDropMode.InternalMove)  # 僅允許內部拖曳

        # 綁定 selection model 的 signal
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        """當選取變更時，發送 signal
        """
        selected_indexes = self.selectionModel().selectedIndexes()
        selected_items: Dict[str, QModelIndex] = {
            self.comic_list_model.data(i, Qt.ItemDataRole.DisplayRole): i for i in selected_indexes
        }
        self.selectionChangedSignal.emit(selected_items)

    def setComicList(self, comicList: List[str]) -> None:
        """設定漫畫清單

        Args:
            comicList (List[str]): 漫畫清單
        """
        self.comic_list_model.setStringList(comicList)

    def dropEvent(self, event: QDropEvent) -> None:
        """重寫 dropEvent，支援多選拖曳排序
        """
        if not event.isAccepted() and event.source() == self:
            pos = event.position().toPoint()
            drop_index = self.indexAt(pos)

            if not drop_index.isValid():
                # 如果拖到空白處，就視為最後
                drop_row = self.comic_list_model.rowCount()
            else:
                # 拖到項目上面 → 插入到它的後面（不是覆蓋）
                drop_row = drop_index.row() + 1

            selected_indexes = sorted(
                self.selectionModel().selectedIndexes(),
                key=lambda x: x.row()
            )

            if not selected_indexes:
                return

            items: List[str] = [self.comic_list_model.data(i, Qt.ItemDataRole.DisplayRole) for i in selected_indexes]

            # 先移除原本的項目（從後往前刪避免 index 錯亂）
            for i in reversed(selected_indexes):
                self.comic_list_model.removeRow(i.row())

            # 計算新的 drop_row（刪掉項目後，位置可能會往前縮）
            rows_above = sum(1 for i in selected_indexes if i.row() < drop_row)
            drop_row -= rows_above

            # 插入到目標位置
            for offset, text in enumerate(items):
                self.comic_list_model.insertRow(drop_row + offset)
                self.comic_list_model.setData(
                    self.comic_list_model.index(drop_row + offset),
                    text
                )

            event.accept()
        else:
            super().dropEvent(event)
