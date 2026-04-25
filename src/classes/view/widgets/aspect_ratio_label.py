from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class AspectRatioLabel(QLabel):
    def __init__(self, content=None):
        super().__init__()
        
        # 1. 初始化變數
        self.original_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(1, 1)

        # 2. 判斷傳入的是 QPixmap 還是字串 (或 None)
        if isinstance(content, QPixmap):
            self.original_pixmap = content
            self.update_pixmap()
        elif isinstance(content, str):
            self.setText(content)  # 如果是字串，直接顯示文字
        
    def setPixmap(self, p):
        # 確保外部呼叫 setPixmap 時能更新原始圖檔
        if isinstance(p, QPixmap):
            self.original_pixmap = p
            self.update_pixmap()
        else:
            super().setPixmap(p)

    def update_pixmap(self):
        # 這裡的邏輯就不會報錯了，因為 original_pixmap 只會是 QPixmap 或 None
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled = self.original_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)

    def resizeEvent(self, event):
        if self.original_pixmap:
            self.update_pixmap()
        super().resizeEvent(event)