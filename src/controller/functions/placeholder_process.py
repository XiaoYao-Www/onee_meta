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
from src.common.unity_function import parseNamespacedKey
from src.classes.controller.comic_placeholder_data import ComicPlaceholderData
from src.classes.view.widgets.smart_integer_field import SmartIntegerField
from src.classes.model.comic_data import XmlComicInfo
from src.view.tabs.info_editor_config import infoEditorTabConfig


def placeholderReplace(text: str, placeholderData: ComicPlaceholderData) -> str:
    """文字替換佔位符
    支援 Python 格式化語法，如 {index:03d}

    Args:
        text (str): 字串
        placeholderData (dict): 佔位符資料

    Returns:
        str: 字串
    """
    def repl(match: re.Match):
        key = match.group(1)
        fmt = match.group(2)
        
        if key not in placeholderData:
            return match.group(0)
            
        value = placeholderData[key]
        
        if fmt:
            try:
                return format(value, fmt)
            except ValueError:
                return str(value)
        
        return str(value)
    
    # 匹配 {key} 或 {key:format}
    pattern = re.compile(r"{(\w+)(?::([^}]+))?}")
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
    for section, fields in infoEditorTabConfig.items():
        for field_key, field_cfg in fields.items():
            if not(field_cfg["type"] == QLineEdit or field_cfg["type"] == QTextEdit or field_cfg["type"] == SmartIntegerField):
                continue
            namespace, key = parseNamespacedKey(field_cfg["info_key"]) # 分析命名空建和鍵值
            if not(namespace in newXmlData["fields"] and key in newXmlData["fields"][namespace]):
                # 處理資料沒有指定項目
                continue
            newXmlData["fields"][namespace][key] = placeholderReplace(cast(str, newXmlData["fields"][namespace][key]), placeholderData)
    # 回傳資料
    return newXmlData