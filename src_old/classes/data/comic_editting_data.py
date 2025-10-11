from typing import TypedDict, List, Dict, Union, NotRequired
from src.classes.data.comic_info_data import ComicInfoData


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
    original_info: ComicInfoData

    """
        編輯中資料
    """
    editting_info: ComicInfoData