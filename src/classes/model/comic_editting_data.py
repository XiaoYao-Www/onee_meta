#####
# 編輯中資料
#####
from typing import TypedDict, List, Dict, Union, NotRequired
from classes.model.comic_data import ComicData


class ComicEdittingData(TypedDict):
    """漫畫編輯資料
    """

    """
        UUID
    """
    uuid: str

    """
        修前資料
    """
    original_data: ComicData

    """
        編輯中資料
    """
    editting_data: NotRequired[ComicData]