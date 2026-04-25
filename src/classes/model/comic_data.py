#####
# 漫畫資料類型
#####
from PySide6.QtGui import QPixmap
from typing import TypedDict, List, Dict, Union, NotRequired


class XmlComicInfo(TypedDict):
    """
        命名空間
        {
            命名空間: 連結,
            命名空間: 連結,
        }
    """
    nsmap: Dict[str, str]

    """
        資料
        {
            命名空間: {
                資料名稱: 值,
                資料名稱: 值,
            },
            命名空間: {
                資料名稱: 值,
                資料名稱: 值,
            },
        }
    """
    fields: Dict[
                str, # 命名空間
                Dict[
                    str, # 資料名稱
                    Union[str, None]
                ]
            ]

class ComicData(TypedDict):
    """漫畫資料格式
    """

    """
        UUID
    """
    uuid: str

    """
        漫畫路徑(相對)
    """
    comic_path: str

    """
        原 ComicInfo.xml 所在相對路徑
    """
    comicInfo_path: NotRequired[str]

    """
        Xml資料
    """
    xml_comic_info: XmlComicInfo

    """
       圖片數量
    """
    image_count: int

    """
        第一張圖片
    """
    first_image: QPixmap | None