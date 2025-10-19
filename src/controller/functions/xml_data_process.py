#####
# xmlData處理
#####
from typing import Any
import copy
# 自訂庫
from src.classes.model.comic_data import XmlComicInfo


def updataXmlComicInfo(origin: XmlComicInfo, updata: XmlComicInfo) -> None:
    """更新XmlComicData
        不回傳鍵 => keep
        回傳 "" => clear
        回傳值 => value

    Args:
        origin (XmlComicInfo): 原資料
        updata (XmlComicInfo): 更新資料
    """
    # 更新 nsmap
    for namespace, url in updata["nsmap"].items():
        # 刪除
        if url == "" and namespace in origin["nsmap"]:
            del origin["nsmap"][namespace]
        # 替換
        else:
            origin["nsmap"][namespace] = url
    # 更新 fields
    for fieldNamespace, fields in updata["fields"].items():
        # 補足 namespace
        if not(fieldNamespace in origin["fields"]):
            origin["fields"][fieldNamespace] = {}
        # 遍歷 fields
        for field, value in fields.items():
            # 刪除
            if value == "" and field in origin["fields"][fieldNamespace]:
                del origin["fields"][fieldNamespace][field]
            # 替換
            else:
                origin["fields"][fieldNamespace][field] = value
        # 清除空 namespace
        if origin["fields"][fieldNamespace] == {}:
            del origin["fields"][fieldNamespace]