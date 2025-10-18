#####
# xmlData處理
#####
from typing import Any
import copy
# 自訂庫
from src.classes.model.comic_data import XmlComicInfo


def updataXmlComicInfo(origin: XmlComicInfo, updata: XmlComicInfo) -> XmlComicInfo:
    """更新XmlComicData(傳回副本)
        不回傳鍵 => keep
        回傳 "" => clear
        回傳值 => value

    Args:
        origin (XmlComicInfo): 原資料
        updata (XmlComicInfo): 更新資料

    Returns:
        XmlComicInfo: 更新完成副本
    """
    newXmlData = copy.deepcopy(origin)
    # 更新 original_path
    if "original_path" in updata:
        newXmlData["original_path"] = updata["original_path"]
    # 更新 nsmap
    for namespace, url in updata["nsmap"].items():
        # 刪除
        if url == "" and namespace in newXmlData["nsmap"]:
            del newXmlData["nsmap"][namespace]
        # 替換
        else:
            newXmlData["nsmap"][namespace] = url
    # 更新 fields
    for fieldNamespace, fields in updata["fields"].items():
        # 補足 namespace
        if not(fieldNamespace in newXmlData["fields"]):
            newXmlData["fields"][fieldNamespace] = {}
        # 遍歷 fields
        for field, value in fields.items():
            # 刪除
            if value == "" and field in newXmlData["fields"][fieldNamespace]:
                del newXmlData["fields"][fieldNamespace][field]
            # 替換
            else:
                newXmlData["fields"][fieldNamespace][field] = value
        # 清除空 namespace
        if newXmlData["fields"][fieldNamespace] == {}:
            del newXmlData["fields"][fieldNamespace]

    return newXmlData