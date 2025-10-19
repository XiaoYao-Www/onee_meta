#####
# 佔位符處理
#####
from typing import Any, cast
import re
import copy
from PySide6.QtWidgets import (
    QLineEdit, QTextEdit, QComboBox
)
# 自訂庫
from src.functions.unity_function import parseNamespacedKey
from src.classes.controller.comic_placeholder_data import ComicPlaceholderData
from src.classes.view.widgets.smart_integer_field import SmartIntegerField
from src.classes.model.comic_data import XmlComicInfo
import src.app_config as APP_CONFIG


def placeholderReplace(text: str, placeholderData: ComicPlaceholderData) -> str:
    """文字替換佔位符

    Args:
        text (str): 字串
        placeholderData (dict): 佔位符資料

    Returns:
        str: 字串
    """
    def repl(match: re.Match):
        key = match.group(1)
        return str(placeholderData.get(key, match.group(0)))
    
    pattern = re.compile(r"{(\w+)}")
    return pattern.sub(repl, text)

def XmlDataPlaceholderProcess(xmlData: XmlComicInfo, placeholderData: ComicPlaceholderData) -> XmlComicInfo:
    """將XML資訊做佔位符替換(回傳拷貝物件)

    Args:
        xmlData (XmlComicInfo): XML資料
        placeholderData (ComicPlaceholderData): 佔位符資料

    Returns:
        XmlComicInfo: XML資料
    """
    newXmlData = copy.deepcopy(xmlData)
    # 處理資料
    for section, fields in APP_CONFIG.infoEditorTabConfig.items():
        for field_key, field_cfg in fields.items():
            if not(field_cfg["type"] == QLineEdit or field_cfg["type"] == QTextEdit):
                #　只處理文字類型
                continue
            namespace, key = parseNamespacedKey(field_cfg["info_key"]) # 分析命名空建和鍵值
            if not(namespace in newXmlData["fields"] and key in newXmlData["fields"][namespace]):
                # 處理資料沒有指定項目
                continue
            newXmlData["fields"][namespace][key] = placeholderReplace(cast(str, newXmlData["fields"][namespace][key]), placeholderData)
    # 回傳資料
    return newXmlData