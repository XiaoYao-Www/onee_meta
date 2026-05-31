#####
# 執行時數據儲存類 (Qt-native)
#####
from typing import Any, Dict, Optional, TypeVar

from PySide6.QtCore import QObject, Signal

from src.logging_config import get_logger

_log = get_logger(__name__)

T = TypeVar('T')


class DataStore(QObject):
    """數據存儲類 — Qt 原生化

    所有讀寫必須發生在主執行緒。
    ※ 取得的資料並非副本，修改須謹慎。
    """

    # 發出 (變動資料字典)
    dataChanged = Signal(dict)

    def __init__(self, store_id: Optional[str] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._store_id: Optional[str] = store_id
        self._data: Dict[str, Any] = {}

    # ── 屬性 ────────────────────────────────────────────

    @property
    def data(self) -> Dict[str, Any]:
        """獲取全部資料 (非副本)"""
        return self._data

    @property
    def id(self) -> Optional[str]:
        """容器 ID"""
        return self._store_id

    # ── 訂閱 (向後相容 API) ──────────────────────────────

    def subscribe(self, callback: "Callable[[Dict[str, Any], Optional[str]], None]") -> "Callable":  # noqa: F821
        """訂閱數據變更

        callback 簽章: callback(changes: dict, store_id: str | None)
        回傳 wrapper，可傳入 dataChanged.disconnect(wrapper) 斷開。
        """
        store_id = self._store_id

        def _wrapper(changes: Dict[str, Any]) -> None:
            try:
                callback(changes, store_id)
            except Exception:
                _log.exception("[DataStore:%s] 回調錯誤，鍵: %s", store_id, list(changes.keys()))

        self.dataChanged.connect(_wrapper)
        return _wrapper

    def unsubscribe(self, wrapper: "Callable") -> None:  # noqa: F821
        """取消訂閱 — 傳入 subscribe() 回傳的 wrapper"""
        try:
            self.dataChanged.disconnect(wrapper)
        except (TypeError, RuntimeError):
            _log.debug("[DataStore:%s] disconnect 失敗（可能已斷開）", self._store_id)

    # ── 資料存取 ─────────────────────────────────────────

    def get(self, key: str, default: Optional[T] = None) -> T:
        """獲取單個值"""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """設置單個值 — 若實際變更才發送 dataChanged"""
        old_value = self._data.get(key)
        if old_value == value:
            return
        self._data[key] = value
        self.dataChanged.emit({key: value})

    def update(self, new_data: Dict[str, Any]) -> None:
        """批量更新 — 只發送實際變更的鍵"""
        changed: Dict[str, Any] = {}
        for key, new_value in new_data.items():
            old_value = self._data.get(key)
            if old_value != new_value:
                self._data[key] = new_value
                changed[key] = new_value
        if changed:
            self.dataChanged.emit(changed)

    def clear(self) -> None:
        """清空所有數據"""
        if not self._data:
            return
        self._data.clear()
        self.dataChanged.emit({})
