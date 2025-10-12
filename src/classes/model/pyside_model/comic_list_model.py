#####
# 漫畫列表模型
#####
from PySide6.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QPersistentModelIndex,
    QMimeData, QDataStream, QByteArray, Signal
)
from typing import Any, cast, Sequence, List, Optional, Callable
# 自訂庫
from src.signal_bus import SIGNAL_BUS
from src.classes.model.data_store import DataStore
from src.classes.model.comic_editting_data import ComicEdittingData

class ComicListModel(QAbstractListModel):
    MIME_TYPE = "application/x-uuiditems"
    """漫畫列表模型
    """
    def __init__(self, uuidList: List[str], comicDataStore: DataStore):
        super().__init__()
        self.uuidList = uuidList # 漫畫UUID列表
        self.comicDataStore = comicDataStore # 漫畫資料儲存
        self.listIndexChange: Optional[Callable[[List[str]], None]] = None  # 列表改動回調

    ###### 基本Model設定

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        """資料長度

        Args:
            parent (QModelIndex | QPersistentModelIndex, optional): 父元件. Defaults to QModelIndex().

        Returns:
            int: 長度
        """
        return len(self.uuidList)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """取得資料

        Args:
            index (QModelIndex | QPersistentModelIndex): 索引
            role (int, optional): 目標身份. Defaults to Qt.ItemDataRole.DisplayRole.

        Returns:
            Any: 資料
        """
        if not index.isValid(): 
            return None
        uuid = self.uuidList[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            # 顯示 序號 + 訊息
            edittingData: ComicEdittingData = cast(ComicEdittingData, self.comicDataStore.get(uuid, {}))
            return edittingData.get("original_data").get("comic_path")
        return None
    
    ###### 權限設置

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        """拖曳設定

        Args:
            index (QModelIndex | QPersistentModelIndex): 索引

        Returns:
            Qt.ItemFlag: 旗標
        """
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemFlag.ItemIsDragEnabled # 允許拖曳
        else:
            return default_flags | Qt.ItemFlag.ItemIsDropEnabled # 允許放置

    def supportedDropActions(self) -> Qt.DropAction:
        """拖曳放置行為

        Returns:
            _type_: 允許行為
        """
        return Qt.DropAction.MoveAction
    
    ###### Drag: 把要拖的 row 編成 MIMEData
    def mimeTypes(self) -> List[str]:
        """拖曳資料類型

        Returns:
            list[str]: 類型列表
        """
        return [self.MIME_TYPE]

    def mimeData(self, indexes: Sequence[QModelIndex]) -> QMimeData:
        """取得拖曳資料

        Args:
            indexes (Sequence[QModelIndex]): 拖曳索引

        Returns:
            QMimeData: 拖曳資料
        """
        # indexes 可能包含同一 row 的多個 column，取獨立 row 並排序
        rows = sorted(set(idx.row() for idx in indexes if idx.isValid()))
        # 創建資料容器
        ba = QByteArray()
        ds = QDataStream(ba, QDataStream.OpenModeFlag.WriteOnly)
        # 寫入資料總數
        ds.writeInt32(len(rows))
        # 寫入每筆row
        for r in rows:
            ds.writeInt32(r)
        # 包裝Mime
        md = QMimeData()
        md.setData(self.MIME_TYPE, ba)
        return md
    
    ###### Drop: 從 MIMEData 解析並重新排列 uuidList
    def dropMimeData(self, mime: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex | QPersistentModelIndex) -> bool:
        """放置拖曳資料

        Args:
            mime (QMimeData): 拖曳資料
            action (Qt.DropAction): 拖曳行為
            row (int): 拖曳目標列
            column (int): 拖曳目標行
            parent (QModelIndex | QPersistentModelIndex): 拖曳目標父類

        Returns:
            bool: 拖曳結果
        """
        # 拖曳資料格式檢查
        if not mime.hasFormat(self.MIME_TYPE):
            return False
        
        # 拖曳類型檢查
        if action != Qt.DropAction.MoveAction:
            return False
        
        # 讀取資料
        ba = mime.data(self.MIME_TYPE)
        ds = QDataStream(ba, QDataStream.OpenModeFlag.ReadOnly)
        count = ds.readInt32()
        rows = [ds.readInt32() for _ in range(count)]
        rows = sorted(set(rows))

        # 沒有資料要搬移，回傳False
        if not rows:
            return False
        
        # 儲存被拖曳UUID
        selectUuid = [self.uuidList[row] for row in rows]
        
        # 計算目的 insert_row
        insert_row = row if row != -1 else self.rowCount()

        # 取要搬移的項目，保持原本相對順序
        moving_items = [self.uuidList[r] for r in rows]

        # 從大到小刪除原始項目（避免索引位移問題）
        for r in reversed(rows):
            self.uuidList.pop(r)

        # 調整插入位置：原本在插入位置之前被刪掉的行會讓插入索引減少
        num_removed_before = sum(1 for r in rows if r < insert_row)
        adjusted_insert = max(0, insert_row - num_removed_before)

        # 插回去（保持順序）
        for i, it in enumerate(moving_items):
            self.uuidList.insert(adjusted_insert + i, it)

        # 要求ListView刷新
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()
        # 列表改動通知
        if self.listIndexChange != None:
            self.listIndexChange(selectUuid)
        return True