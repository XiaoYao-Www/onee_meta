from PySide6.QtCore import QObject, Signal

class _UISignals(QObject):
    """UI 調用訊號
    """
    sendCritical = Signal(str, str)
    sendInformation = Signal(str, str)
    retranslateUi = Signal()

class _AppSettingSignals(QObject):
    """應用設定訊號
    """
    fontSizeChanged = Signal(int)

    def __init__(self):
        super().__init__()

class _SignalBus(QObject):
    """信號總線
    """

    def __init__(self):
        super().__init__()
        self.appSetting = _AppSettingSignals()
        self.ui = _UISignals()

SIGNAL_BUS = _SignalBus()
