#####
# 漫畫佔位符資料
#####
from typing import TypedDict

class ComicPlaceholderData(TypedDict):
    """漫畫佔位符資料
    """
    index: int # 列表絕對位置
    order: int # 選中項相對位置