#####
# 漫畫資料處理
#####
from typing import Optional, Dict
import lxml.etree as ET
from lxml.builder import ElementMaker
import os
import zipfile

# 自訂庫
from src.classes.model.comic_data import XmlComicInfo


def xml2Data(xmlContext: bytes) -> XmlComicInfo:
    """解析XML為漫畫資訊資料

    Args:
        xmlContext (bytes): XML資料

    Returns:
        XmlComicInfo: 漫畫資料
    """
    # 解析錯誤回傳空資料
    try:
        tree = ET.fromstring(xmlContext)
    except Exception as e:
        return {
            "nsmap": {},
            "fields": {},
        }

    # 資料解析
    nsmap: Dict[str, str] = tree.nsmap.copy()
    data: XmlComicInfo = {
        "nsmap": nsmap,
        "fields": {},
    }
    ## 額外補漏命名空間（在 XML 內部宣告，但 root 沒宣告的）
    for elem in tree.iter():
        prefix = elem.prefix # 名稱
        ns_uri = ET.QName(elem).namespace # 連結

        if prefix and ns_uri and prefix not in data["nsmap"]:
            data["nsmap"][prefix] = ns_uri

    ## 解析資料
    for elem in tree.iterchildren():
        prefix = elem.prefix or "base"
        tag = ET.QName(elem).localname
        text = elem.text.strip() if elem.text else ''

        if prefix not in data["fields"]:
            data["fields"][prefix] = {}
        data["fields"][prefix][tag] = text
    
    return data

def data2Xml(comicData: XmlComicInfo) -> bytes:
    """將資料轉成XML

    Args:
        comicData (XmlComicInfo): 漫畫資料

    Returns:
        bytes: XML資料
    """
    nsmap = comicData.get("nsmap", {})
    
    # 根元素保留所有 namespace 宣告
    root = ET.Element("ComicInfo", nsmap=nsmap)

    # 處理單值欄位
    for prefix, fields in comicData.get("fields", {}).items():
        for tag, value in fields.items():
            if value == '' or value == None:
                continue  # 忽略空值

            value_str = str(value).strip()
            if prefix == 'base':
                # base prefix 無 namespace，直接新增子元素
                el = ET.SubElement(root, tag)
                el.text = value_str
            else:
                # 強制使用指定前綴（即使 namespace URI 相同）
                ns_uri = nsmap[prefix]
                qname = ET.QName(ns_uri, tag)  # 建立帶前綴的 QName
                el = ET.SubElement(root, qname.text, nsmap={prefix: ns_uri})
                el.text = value_str

    return ET.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)