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
                background: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 9px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4facfe, stop: 1 #00f2fe
                );
                border-radius: 9px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            LoadingDialog {
                background-color: rgba(30, 30, 40, 220);
                border-radius: 12px;
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
