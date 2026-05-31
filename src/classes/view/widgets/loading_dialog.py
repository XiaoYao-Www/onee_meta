from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QLabel, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal

from src.layout_constants import LOADING_DIALOG_WIDTH, LOADING_DIALOG_HEIGHT


class LoadingDialog(QDialog):
    """處理中提示 — 支援進度條"""

    def __init__(self, info: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        # 訊息文字
        self.infoLabel = QLabel(info, self)
        self.infoLabel.setStyleSheet("QLabel { color: white; font-size: 16px; }")
        self.infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.infoLabel)

        # 進度條
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # 0 = 不確定模式 (動畫)
        self.progress_bar.setFixedWidth(260)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background: #7c7c80;
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            LoadingDialog {
                background-color: rgba(28, 28, 30, 230);
                border-radius: 14px;
            }
        """)
        self.resize(LOADING_DIALOG_WIDTH, LOADING_DIALOG_HEIGHT)

    def setInfoText(self, info: str) -> None:
        """設置訊息文字"""
        self.infoLabel.setText(info)

    def setProgress(self, current: int, total: int, message: str = "") -> None:
        """設定進度 — 切換到確定模式

        Args:
            current: 當前進度 (0-based)
            total: 總數
            message: 可選的進度訊息
        """
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        if message:
            self.infoLabel.setText(message)
