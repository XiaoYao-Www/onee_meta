from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt


# ==========================================
# 1. 自訂可點擊的 Label
# ==========================================
class ClickableLabel(QLabel):
    # 定義一個訊號，當被點擊時發送 (欄位名稱, 內容值)
    clicked = Signal(str, str)

    def __init__(self, field_name, text_value, display_text=None, parent=None):
        super().__init__(f"<b>{field_name}:</b> {text_value}" if display_text is None else display_text, parent)
        self.field_name = field_name
        self.text_value = text_value
        
        # 讓滑鼠游標移過去時變成手指形狀
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # 設定基本的 Hover 效果

    def mouseReleaseEvent(self, event):
        # 當滑鼠放開時，觸發 clicked 訊號
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.field_name, self.text_value)
        super().mouseReleaseEvent(event)