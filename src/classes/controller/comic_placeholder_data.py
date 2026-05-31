#####
# 漫畫佔位符資料
#####
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComicPlaceholderData:
    """漫畫佔位符資料

    支援 dict-style 存取 (placeholder["index"]) 以向後相容。
    """

    index: int = 0           # 列表絕對位置
    order: int = 0           # 選中項相對位置
    file_name: str = ""      # 檔案名稱（不含副檔名）
    file_ext: str = ""       # 檔案副檔名
    parent_folder: str = ""  # 父資料夾名稱
    year: str = ""           # 年
    month: str = ""          # 月
    day: str = ""            # 日
    date: str = ""           # 完整日期 (YYYY-MM-DD)
    clear_old_title: str = ""  # 整理過的舊名稱
    image_count: int = 0     # 圖片數量

    # ── 向後相容 dict-style 存取 ────────────────────────

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if not hasattr(self, key):
            raise KeyError(key)
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)
