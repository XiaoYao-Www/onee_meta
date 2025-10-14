#####
# 可點擊連結按鈕
#####
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont

class ClickableUrlLabel(QLabel):
    """ 可點擊連結 """
    def __init__(self, text, url, parent=None):
        super().__init__(text, parent=parent)
        self.url = url
        self.setStyleSheet("""
            QLabel {
                color: #0366d6;  /* GitHub 链接蓝 */
                text-decoration: underline;
            }
            QLabel:hover {
                color: #1a7f37;  /* GitHub 悬停绿 */
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setOpenExternalLinks(False)  # 禁用默認連結處理

    def mousePressEvent(self, event):
        QDesktopServices.openUrl(QUrl(self.url))