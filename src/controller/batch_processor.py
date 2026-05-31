"""
批次處理器 — 將編輯器中的變更套用到選取的漫畫
"""
import copy
import os
from datetime import datetime
from typing import List, cast

from src.classes.model.comic_data import ComicData, XmlComicInfo
from src.classes.controller.comic_placeholder_data import ComicPlaceholderData
from src.controller.functions.placeholder_process import XmlDataPlaceholderProcess
from src.controller.functions.xml_data_process import updataXmlComicInfo
from src.logging_config import get_logger

_log = get_logger(__name__)


class BatchResult:
    """批次處理結果"""
    def __init__(self, success_count: int, fail_count: int, total: int) -> None:
        self.success = success_count
        self.fail = fail_count
        self.total = total

    @property
    def all_success(self) -> bool:
        return self.fail == 0


class BatchProcessor:
    """將編輯資料批次寫入所選漫畫"""

    def __init__(self, comic_data_store, running_store, write_comic_fn) -> None:
        self._comic_store = comic_data_store      # DataStore[uuid → ComicData]
        self._running = running_store             # DataStore
        self._write_comic = write_comic_fn        # (uuid) -> bool

    def process(self, editor_data: XmlComicInfo) -> BatchResult:
        """執行批次寫入

        Args:
            editor_data: 編輯器中組合好的 XmlComicInfo

        Returns:
            BatchResult: 成功/失敗統計
        """
        uuid_select: list[str] = self._running.get("selected_comics", [])
        comic_all_list: list[str] = self._running.get("comic_uuid_list", [])

        if not uuid_select or not comic_all_list:
            return BatchResult(0, 0, 0)

        fail_count = 0

        for order, uuid in enumerate(uuid_select, start=1):
            comic_data = self._comic_store.get(uuid)
            if comic_data is None:
                fail_count += 1
                continue

            placeholder = self._build_placeholder(
                uuid=uuid,
                order=order,
                comic_data=comic_data,
                uuid_list=comic_all_list,
            )

            # 佔位符替換
            processed: XmlComicInfo = XmlDataPlaceholderProcess(editor_data, placeholder)

            # 備份 → 更新 → 寫入
            old_xml = comic_data.get("xml_comic_info")
            if old_xml is None:
                fail_count += 1
                continue

            backup = copy.deepcopy(old_xml)
            updataXmlComicInfo(old_xml, processed)

            if not self._write_comic(uuid):
                comic_data["xml_comic_info"] = backup
                fail_count += 1

        return BatchResult(
            success_count=len(uuid_select) - fail_count,
            fail_count=fail_count,
            total=len(uuid_select),
        )

    @staticmethod
    def _build_placeholder(
        uuid: str,
        order: int,
        comic_data: ComicData,
        uuid_list: List[str],
    ) -> ComicPlaceholderData:
        """根據漫畫資料建立佔位符物件"""
        filename_full = os.path.basename(comic_data["comic_path"])
        file_name, file_ext = os.path.splitext(filename_full)
        parent_folder = os.path.basename(os.path.dirname(comic_data["comic_path"]))
        now = datetime.now()

        raw_title = (
            comic_data.get("xml_comic_info", {})
            .get("fields", {})
            .get("base", {})
            .get("Title", "")
        )
        clear_title = str(raw_title).replace(" 🔒", "").replace("🔒", "")

        return ComicPlaceholderData(
            index=uuid_list.index(uuid) + 1,
            order=order,
            file_name=file_name,
            file_ext=file_ext,
            parent_folder=parent_folder,
            year=str(now.year),
            month=f"{now.month:02d}",
            day=f"{now.day:02d}",
            date=now.strftime("%Y-%m-%d"),
            clear_old_title=clear_title,
            image_count=comic_data.get("image_count", 0),
        )
