#####
# 自訂智慧整數輸入框
#####
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QIntValidator
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
        self._state = "clear"  # 初始狀態為清除

    def _on_text_changed(self, text: str) -> None:
        """確認輸入狀態

        Args:
            text (str): 輸入文字
        """
        text = text.strip()
        if text == "":
            self._state = "clear"
        elif text == "{keep}":
            self._state = "preserve"
        elif text in "{keep}":
            if self._state == "preserve":
                self.setValue("")
            else:
                self.setValue("{keep}")
        elif text.isdigit():
            if int(text) >= 0:
                self._state = "value"
            else:
                self.setText("")
                self._state = "clear" 
        else:
            self.setText("")
            self._state = "clear"

    def value(self) -> None | int:
        """取得數值

        Raises:
            ValueError: _description_

        Returns:
            None | int: 數值
        """
        if self._state == "value":
            return int(self.text().strip())
        else:
            return None

    def setValue(self, value: int | str) -> str:
        """設定數值

        Args:
            value (int | str): 數值

        Returns:
            str: 狀態
        """
        if value == "{keep}":
            self._state = "preserve"
            self.setText("{keep}")
        elif type(value) == int:
            if value >= 0:
                self._state = "value"
                self.setText(str(value))
            else:
                self._state = "clear"
                self.setText("")
        else:
            self._state = "clear"
            self.setText("")
        return self._state

    def get_state(self) -> str:
        """回傳狀態

        Returns:
            str: 狀態
        """
        return self._state
