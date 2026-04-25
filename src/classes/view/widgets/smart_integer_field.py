#####
# 自訂智慧整數輸入框
#####
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QIntValidator
import re
# 自訂庫
from src.translations import TR
from src.signal_bus import SIGNAL_BUS

class SmartIntegerField(QLineEdit):
    """自訂數字輸入
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText(TR.UI_WIDGETS["輸入{keep}保留原值"]())
        SIGNAL_BUS.uiRevice.translateUi.connect( # 翻譯處理
            lambda: self.setPlaceholderText(TR.UI_WIDGETS["輸入{keep}保留原值"]())
        )
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str) -> None:
        """確認輸入狀態

        Args:
            text (str): 輸入文字
        """
        text = text.strip()
        if text == "{":
            self.setValue("{}")
        elif re.fullmatch(r"^\{[a-zA-Z0-9_]*\}$", text):
            pass
        elif text.isdigit():
            if int(text) >= 0:
                pass
            else:
                self.setText("")
        else:
            self.setText("")

    def value(self) -> str:
        """取得數值

        Raises:
            ValueError: _description_

        Returns:
            None | int: 數值
        """
        return self.text().strip()

    def setValue(self, value: int | str) -> str:
        """設定數值

        Args:
            value (int | str): 數值

        Returns:
            str: 狀態
        """
        self.setText(str(value))
        return self.text().strip()