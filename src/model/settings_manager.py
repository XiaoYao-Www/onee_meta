"""
應用設定管理 — 負責持久化讀寫 app_setting.json
"""
import json
import os
from typing import Any, Dict, Optional

from src.classes.model.data_store import DataStore
from src.logging_config import get_logger

_log = get_logger(__name__)


class SettingsManager:
    """封裝應用設定的讀寫與 DataStore

    用法:
        mgr = SettingsManager("assets/app_setting.json")
        mgr.store.set("font_size", 12)   # 自動觸發儲存
        font = mgr.store.get("font_size")
    """

    def __init__(self, json_path: str, defaults: Optional[Dict[str, Any]] = None) -> None:
        self._json_path = json_path
        self.store = DataStore(store_id="app_settings")

        # 載入既有設定
        old = self._read_json()

        # 合併預設值
        merged: Dict[str, Any] = {}
        if defaults:
            merged.update(defaults)
        merged.update(old)

        self.store.update(merged)

        # 訂閱變更 → 自動寫入 JSON（保存 wrapper 以便必要時 disconnect）
        self._sub_handle = self.store.subscribe(self._on_changed)

    # ── 內部 ────────────────────────────────────────────

    def _read_json(self) -> Dict[str, Any]:
        if not os.path.exists(self._json_path):
            with open(self._json_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
            return {}

        with open(self._json_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                _log.warning("設定檔損壞，重置為空")
                return {}

    def _on_changed(self, _changes: Dict[str, Any], _store_id: Optional[str]) -> None:
        with open(self._json_path, "w", encoding="utf-8") as f:
            json.dump(self.store.data, f, ensure_ascii=False, indent=4)
