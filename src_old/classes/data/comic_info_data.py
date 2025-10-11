from typing import TypedDict, List, Dict, Union, NotRequired


class XmlComicInfo(TypedDict):
    """
        原 ComicInfo.xml 所在相對路徑
    """
    original_path: NotRequired[str]

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

class ComicInfoData(TypedDict):
    """漫畫資料格式
    """

    """
        漫畫路徑
    """
    comic_path: str

    """
        Xml資料
    """
    xml_comic_info: XmlComicInfo