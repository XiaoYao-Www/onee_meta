#####
# 主model
#####
import os
from pathlib import Path
from typing import Dict, List, Optional
from natsort import natsorted
# 自訂庫
import src.app_config as APP_CONFIG
from src.classes.model.data_store import DataStore
from src.classes.model.comic_data import ComicData
from src.model.settings_manager import SettingsManager
from src.model.functions.comic_read_write import readComicFolder, writeComicData
from src.classes.model.pyside_model.comic_list_model import ComicListModel


class MainModel:
    """主後端儲存 — 統籌漫畫資料與應用狀態"""

    def __init__(self) -> None:
        # ── 應用設定 (由 SettingsManager 管理持久化) ──
        self._settings = SettingsManager(
            APP_CONFIG.appSettingJsonPath,
            defaults={
                "font_size": 10,
                "lang": "",
                "image_exts": [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"],
                "allow_files": [".nomedia"],
                "calibre_path": "",
                "dual_comic_layout": 0,
            },
        )
        # 向後相容別名
        self.appSetting = self._settings.store

        # ── 翻譯檔案 ──
        translation_files = self._read_lang_files()

        # ── 運行時資料 ──
        self.runningStore = DataStore(store_id="runtime")
        self.runningStore.update({
            "translation_files": translation_files,
            "comic_folder_path": "",
            "comic_uuid_list": [],
            "selected_comics": [],
        })

        # ── 漫畫資料儲存 & ListView Model ──
        self.comicDataStore = DataStore(store_id="comics")
        self.comicListModel = ComicListModel(
            self.runningStore.get("comic_uuid_list", []),
            self.comicDataStore,
        )

    # ── 漫畫列表排序 ───────────────────────────────────

    def comicListSorted(self, sort_type: int) -> None:
        """排序漫畫列表

        Args:
            sort_type: 1 = 自然排序(檔名), 2 = 集數排序
        """
        def _basename(uuid: str) -> str:
            data = self.comicDataStore.get(uuid)
            return Path(data["comic_path"]).name if data else ""

        def _number(uuid: str) -> int:
            data = self.comicDataStore.get(uuid)
            if not data:
                return -1
            num_str = data.get("xml_comic_info", {}).get("fields", {}).get("base", {}).get("Number") or ""
            try:
                return int(num_str)
            except (ValueError, TypeError):
                return -1

        self.comicListModel.beginResetModel()
        try:
            uuid_list: list[str] = self.runningStore.get("comic_uuid_list", [])
            if sort_type == 1:
                uuid_list[:] = natsorted(uuid_list, key=_basename)
            elif sort_type == 2:
                uuid_list.sort(key=_number)
        finally:
            self.comicListModel.endResetModel()

    # ── 檔案讀寫 ──────────────────────────────────────

    def readComicFolder(self, comicFolderPath: str) -> None:
        """載入漫畫資料夾內容"""
        self.runningStore.set("comic_folder_path", comicFolderPath)

        comic_editting_data: Dict[str, ComicData] = readComicFolder(
            comicFolderPath,
            self.appSetting.get("image_exts", []),
            self.appSetting.get("allow_files", []),
        )

        self.comicDataStore.clear()
        self.comicDataStore.update(comic_editting_data)

        self.comicListModel.beginResetModel()
        self.runningStore.set("comic_uuid_list", list(comic_editting_data.keys()))
        self.comicListModel.uuidList = self.runningStore.get("comic_uuid_list", [])
        self.comicListModel.endResetModel()

    def writeComic(self, uuid: str) -> bool:
        """將漫畫資料寫入成檔案"""
        root_path: str = self.runningStore.get("comic_folder_path", "")
        comic_data: ComicData = self.comicDataStore.get(uuid)
        return writeComicData(root_path, comic_data)

    # ── 翻譯檔 ────────────────────────────────────────

    def _read_lang_files(self) -> Dict[str, str]:
        """掃描 .qm 翻譯檔案 → {語言代碼: 絕對路徑}"""
        folder = Path(APP_CONFIG.translationFilePath)
        return {
            file.name.replace(".qm", ""): str(file.resolve())
            for file in folder.glob("*.qm")
        }
