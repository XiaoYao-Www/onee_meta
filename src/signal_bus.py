from PySide6.QtCore import QObject, Signal

class _UISendSignals(QObject):
    """UI 發送訊號
    """
    selectComicFolder = Signal(str)
    comicListSelected = Signal(list)

    def __init__(self):
        super().__init__()

class _UIReviceSignals(QObject):
    """UI 接受訊號
    """
    translateUi = Signal() # 翻譯更新
    sendCritical = Signal(str, str) # 傳送警告訊息
    sendInformation = Signal(str, str) # 傳送資訊訊息
    
    def __init__(self):
        super().__init__()

class _SettingChange(QObject):
    """設定變更
    """
    fontSize = Signal(int) # 字體大小改變

    def __init__(self):
        super().__init__()

class _SignalBus(QObject):
    """信號總線
    """

    def __init__(self):
        super().__init__()
        self.uiRevice = _UIReviceSignals()
        self.uiSend = _UISendSignals()
        self.settingChange = _SettingChange()

SIGNAL_BUS = _SignalBus()
