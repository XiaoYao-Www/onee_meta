#####
# 自訂文字截斷加提示按鈕
#####
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QApplication, QPushButton, QHBoxLayout, QWidget, QSizePolicy
from typing import Optional

class ElidingButton(QPushButton):
    """自定義按鈕，支援文字截斷和自訂工具提示
    """
    def __init__(
            self,
            text: str = '',
            tooltip: Optional[str] = None,
            minWidth: Optional[int] = None,
            maxWidth: Optional[int] = None, 
            parent=None
        ):
        """初始化

        Args:
            text (str, optional): 按鈕文字. Defaults to ''.
            tooltip (Optional[str], optional): 提示文字. Defaults to None.
            minWidth (Optional[int], optional): 最小寬度. Defaults to None.
            maxWidth (Optional[int], optional): 最大寬度. Defaults to None.
            parent (_type_, optional): 父項. Defaults to None.
        """
        super().__init__(parent)
        self._original_text = text  # 儲存原始文字
        self._tooltip = tooltip if tooltip != None else text  # 設置工具提示，預設為原始文字
        if minWidth != None:
            self.setMinimumWidth(minWidth)  # 最小寬度
        if maxWidth != None:
            self.setMaximumWidth(maxWidth)  # 最大寬度
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # 固定大小策略
        self.setToolTip(self._tooltip)  # 設置初始工具提示
        self.updateText()  # 初始截斷文字

    def setText(self, text: str):
        """設置文字

        Args:
            text (str): 文字
        """
        if self._tooltip == self._original_text:
            self._tooltip = text
            self.setToolTip(self._tooltip)
        self._original_text = text
        self.updateText()

    def setToolTip(self, tooltip: str):
        """設置工具提示

        Args:
            tooltip (str): 文字
        """ 
        self._tooltip = tooltip
        super().setToolTip(tooltip)

    def updateText(self):
        """刷新顯示文字
        """
        # 根據按鈕寬度截斷文字
        metrics = QFontMetrics(self.font())
        available_width = self.width() - self.contentsMargins().left() - self.contentsMargins().right()
        elided_text = metrics.elidedText(self._original_text, Qt.TextElideMode.ElideRight, available_width)
        super().setText(elided_text)

    def resizeEvent(self, event):
        """處理大小變化，動態更新文字
        """
        self.updateText()
        super().resizeEvent(event)