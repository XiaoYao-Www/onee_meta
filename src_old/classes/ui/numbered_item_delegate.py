from typing import Any
from PySide6.QtWidgets import (
    QApplication, QStyledItemDelegate, QStyleOptionViewItem,
    QStyle, QWidget,
)
from PySide6.QtCore import Qt, QRect, QModelIndex, QPersistentModelIndex
from PySide6.QtGui import QPainter


class NumberedItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> None:
        """自訂繪製：在文字前加上四位數序號

        Args:
            painter (QPainter): _description_
            option (QStyleOptionViewItem): _description_
            index (QModelIndex | QPersistentModelIndex): _description_
        """

        painter.save()  # 保存畫筆狀態

        # 獲取資料
        original_text: str = str(index.model().data(index, Qt.ItemDataRole.DisplayRole))
        row_number: int = index.row() + 1
        display_text: str = f"{row_number:04d}. {original_text}"

        # 初始化繪製選項
        new_option = QStyleOptionViewItem(option)
        self.initStyleOption(new_option, index)
        new_option.text = ""  # 清空文本，稍後手動繪製 # type: ignore[attr-defined]

        # 繪製背景（含選中高亮）
        style = (
            new_option.widget.style() # type: ignore[attr-defined]
            if new_option.widget # type: ignore[attr-defined]
            else QApplication.style()
        )
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, new_option, painter, new_option.widget) # type: ignore[attr-defined]

        # 設置文字顏色
        if option.state & QStyle.StateFlag.State_Selected: # type: ignore[attr-defined]
            painter.setPen(option.palette.highlightedText().color()) # type: ignore[attr-defined]
        else:
            painter.setPen(option.palette.text().color()) # type: ignore[attr-defined]

        # 調整文字繪製區域
        text_rect: QRect = option.rect.adjusted(5, 0, -5, 0) # type: ignore[attr-defined]

        # 繪製文字
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_text)

        painter.restore()  # 恢復畫筆狀態
