from PySide6.QtCore import QObject, Signal

class _UISignals(QObject):
    """UI 接受訊號
    """
    sendCritical = Signal(str, str)
    sendInformation = Signal(str, str)
    retranslateUi = Signal()

class _AppSettingSignals(QObject):
    """應用設定訊號
    """
    fontSizeChanged = Signal(int)
    imageExtChanged = Signal(list)
    allowFileChanged = Signal(list)
    langChanged = Signal(str)

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
