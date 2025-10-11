from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QThread, Signal

class LoadingDialog(QDialog):
    """處理中提示
    """
    def __init__(self, info: str, parent=None):
        """初始化

        Args:
            info (str): 顯示提示
            parent (_type_, optional): 父項. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 阻止所有操作
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        self.infoLabel = QLabel(info, self)
        self.infoLabel.setStyleSheet("QLabel { color: white; font-size: 18px; }")
        self.infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.infoLabel)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
        self.resize(200, 100)

    def setInfoText(self, info: str) -> None:
        """設置顯示提示

        Args:
            info (str): 顯示提示
        """
        self.infoLabel.setText(info)