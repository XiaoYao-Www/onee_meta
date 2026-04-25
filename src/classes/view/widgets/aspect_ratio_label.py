from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class AspectRatioLabel(QLabel):
    def __init__(self, content=None):
        super().__init__()
        
        self.original_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        # 設定 MinimumSize 避免 Layout 縮小時將 Label 壓縮到消失
        self.setMinimumSize(1, 1)

        if isinstance(content, QPixmap):
            self.setPixmap(content)
        elif isinstance(content, str):
            self.setText(content)
        
    def setPixmap(self, p: QPixmap | QImage):
        """重新定義 setPixmap，儲存原始圖檔並觸發更新"""
        if not p or p.isNull():
            self.original_pixmap = None
            super().setPixmap(QPixmap())
            return

        self.original_pixmap = p
        self.update_pixmap()

    def update_pixmap(self):
        """執行高品質縮放的核心邏輯"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            # --- 關鍵：處理高 DPI 畫質 ---
            # 獲取當前螢幕的縮放比例 (例如 1.5 或 2.0)
            dpr = self.devicePixelRatioF() 
            
            # 1. 計算目標物理尺寸 (邏輯尺寸 * 比例)
            target_size = self.size() * dpr
            
            # 2. 進行高品質縮放
            scaled = self.original_pixmap.scaled(
                target_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation # 平滑演算法
            )
            
            # 3. 告訴圖片它現在的像素密度是多少，這能防止它被系統二度拉伸
            scaled.setDevicePixelRatio(dpr)
            
            # 呼叫父類的 setPixmap 顯示結果
            super().setPixmap(scaled)

    def resizeEvent(self, event):
        """當 Label 尺寸改變時重新計算縮放"""
        if self.original_pixmap:
            self.update_pixmap()
        super().resizeEvent(event)