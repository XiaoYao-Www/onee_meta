import os
from typing import List, Dict, Optional
import zipfile
# 自訂庫
from src.classes.data.comic_info_data import ComicInfoData
from src.app_config import compressionComicExt
from src.model.functions.comic_info_process import xml2Data, data2Xml

def readComicInfoData(comicPath: str) -> ComicInfoData:
    """讀取漫畫的資訊資料

    Args:
        comicPath (str): 漫畫路徑

    Returns:
        ComicInfoData: 漫畫資料
    """
    try:
        with zipfile.ZipFile(comicPath, 'r') as zf:
            # 取得第一個漫畫資訊檔案
            comicinfo_path = next(
                (name for name in zf.namelist() if name.lower().endswith("comicinfo.xml")),
                None
            )

            if not comicinfo_path:
                return {
                    "nsmap": {},
                    "fields": {},
                }

            with zf.open(comicinfo_path) as f:
                parsed = xml2Data(f.read())
                parsed["original_path"] = comicinfo_path  # 記錄原始 ComicInfo.xml 的路徑
                return parsed

    except Exception as e:
        return {
            "nsmap": {},
            "fields": {},
        }

def readComicFolder(folderPath: str, imgExt: List[str], allowFile: List[str]) -> Dict[str, ComicInfoData]:
    """讀取漫畫資料夾

    Args:
        folderPath (str): 資料夾路徑
        imgExt (List[str]): 圖片附檔名
        allowFile (List[str]): 允許檔案

    Returns:
        Dict[str, ComicInfoData]: 資料字典
    """
    comic_metadata_cache: Dict[str, ComicInfoData] = {}

    if not os.path.isdir(folderPath):
        return {}
    
    for root, dirs, files in os.walk(folderPath):
        folder_is_comic = True
        has_image_file = False
        independent_comic_info_path = ""

        # 若包含任何子資料夾，就不是漫畫資料夾
        if dirs:
            folder_is_comic = False

        # 處理檔案
        for f in files:
            f_lower = f.lower()
            if f_lower.endswith(compressionComicExt):
                # 壓縮檔
                rel_path = os.path.relpath(os.path.join(root, f), folderPath)
                full_path = os.path.join(folderPath, rel_path)
                comic_metadata_cache[rel_path] = readComicInfoData(full_path)
                folder_is_comic = False
            elif f_lower.endswith(tuple(imgExt)):
                # 圖片檔
                has_image_file = True
            elif f_lower == "comicinfo.xml":
                # ComicInfo.xml
                # 取最後一個
                independent_comic_info_path = os.path.abspath(os.path.join(root, f))
            elif f in allowFile:
                # 允許的檔案
                pass
            else:
                # 其餘檔案類型
                folder_is_comic = False

        # 漫畫資料夾處理
        if folder_is_comic and has_image_file:
            rel_path = os.path.relpath(root, folderPath)
            if independent_comic_info_path != "":
                with open(independent_comic_info_path, "rb") as f:
                    parsed: ComicInfoData = xml2Data(f.read())
            else:
                parsed: ComicInfoData = {
                    "nsmap": {},
                    "fields": {},
                }
            comic_metadata_cache[rel_path] = parsed

    return comic_metadata_cache