#####
# 漫畫佔位符資料
#####
from typing import TypedDict

class ComicPlaceholderData(TypedDict):
    """漫畫佔位符資料
    """
    index: int # 列表絕對位置
    order: int # 選中項相對位置
    file_name: str # 檔案名稱(不含副檔名)
    file_ext: str # 檔案副檔名
    parent_folder: str # 父資料夾名稱
    year: str # 年
    month: str # 月
    day: str # 日
    date: str # 完整日期 (YYYY-MM-DD)
    clear_old_title: str # 整理過的舊名稱
    image_count: int # 圖片數量