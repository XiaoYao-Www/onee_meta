#####
# 訊號線
#####
from PySide6.QtCore import QObject, Signal

class _UISendSignals(QObject):
    """UI 發送訊號
    """
    selectComicFolder = Signal(str)
    comicListSelected = Signal(list)
    startProcess = Signal()
    comicListSort = Signal(int)
    # app_setting_tab
    fontSizeSet = Signal(int)
    imgExtensionSet = Signal(list)
    allowFileSet = Signal(list)
    langChange = Signal(str)
    carlibrePathSet = Signal(str)
    runScanner = Signal(str, str, str)

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
    """信號總線 — 應用層全域事件中樞

    使用方式:
        from src.signal_bus import SIGNAL_BUS
        SIGNAL_BUS.uiSend.selectComicFolder.connect(handler)

    測試時可呼叫 reset_signal_bus() 重建實例。
    """

    def __init__(self) -> None:
        super().__init__()
        self.uiRevice = _UIReviceSignals()
        self.uiSend = _UISendSignals()
        self.settingChange = _SettingChange()


# ── 全域實例 ────────────────────────────────────────────

_SIGNAL_BUS: "_SignalBus | None" = None


def _create_bus() -> "_SignalBus":
    return _SignalBus()


def get_signal_bus() -> "_SignalBus":
    """取得目前的 SignalBus 實例（惰性建立）"""
    global _SIGNAL_BUS
    if _SIGNAL_BUS is None:
        _SIGNAL_BUS = _create_bus()
    return _SIGNAL_BUS


def reset_signal_bus() -> "_SignalBus":
    """重建 SignalBus（用於測試隔離）"""
    global _SIGNAL_BUS
    _SIGNAL_BUS = _create_bus()
    return _SIGNAL_BUS


# 模組級捷徑 — 向後相容
SIGNAL_BUS = get_signal_bus()
