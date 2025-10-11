#####
# 漫畫檔案讀寫
#####
import os
from typing import List, Dict, Optional
import zipfile
# 自訂庫
from src.classes.model.comic_data import ComicData, XmlComicInfo
from src.classes.model.comic_editting_data import ComicEdittingData
from src.model.functions.uuid import newUUID4
from src.app_config import compressionComicExt
from model.functions.comic_data_process import xml2Data, data2Xml


def readXmlComicInfo(comicPath: str) -> XmlComicInfo:
    """讀取封裝漫畫的資訊資料

    Args:
        comicPath (str): 漫畫路徑

    Returns:
        XmlComicInfo: 漫畫資料
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

def readComicFolder(folderPath: str, imgExt: List[str], allowFile: List[str]) -> Dict[str, ComicEdittingData]:
    """讀取漫畫資料夾

    Args:
        folderPath (str): 資料夾路徑
        imgExt (List[str]): 圖片附檔名
        allowFile (List[str]): 允許檔案

    Returns:
        Dict[str, ComicEdittingData]: 資料字典
    """
    comic_data_cache: Dict[str, ComicEdittingData] = {}

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
                new_uuid4 = newUUID4(set(comic_data_cache.keys()))
                comic_data_cache[new_uuid4] = {
                    "uuid": new_uuid4,
                    "original_data": {
                        "comic_path": rel_path,
                        "xml_comic_info": readXmlComicInfo(full_path)
                    }
                }
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
                    parsed: XmlComicInfo = xml2Data(f.read())
            else:
                parsed: XmlComicInfo = {
                    "nsmap": {},
                    "fields": {},
                }
            new_uuid4 = newUUID4()
            comic_data_cache[new_uuid4] = {
                "uuid": new_uuid4,
                "original_data": {
                    "comic_path": rel_path,
                    "xml_comic_info": parsed
                }
            }

    return comic_data_cache

# def writeComicInfoData(comicPath: str, data: ComicInfoData) -> bool:
#     """寫入漫畫資訊

#     Args:
#         comicPath (str): 漫畫絕對路徑
#         data (ComicInfoData): 資料

#     Returns:
#         bool: 成功與否
#     """
#     if os.path.isdir(comicPath):
#         return writeComicInfoData_dir(comicPath, data)
#     elif os.path.isfile(comicPath) and comicPath.lower().endswith(compressionComicExt):
#         return writeComicInfoData_zip(comicPath, data)
#     else:
#         return False

# def writeComicInfoData_dir(comicPath: str, data: ComicInfoData) -> bool:
#     """寫入漫畫資訊_資料夾

#     Args:
#         comicPath (str): 漫畫絕對路徑
#         data (ComicInfoData): 資料

#     Returns:
#         bool: 成功與否
#     """
#     temp_zip_path = comicPath + ".tmp"

#     try:
#         with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_STORED) as zout:
#             # 先寫入 ComicInfo.xml
#             zout.writestr("ComicInfo.xml", data2Xml(data))

#             # 走訪整個資料夾結構
#             for root, _, files in os.walk(comicPath):
#                 for file in files:
#                     if file.lower() == "comicinfo.xml":
#                         continue  # 跳過原本的 ComicInfo.xml

#                     full_path = os.path.join(root, file)
#                     rel_path = os.path.relpath(full_path, comicPath)

#                     zout.write(full_path, arcname=rel_path)

#         os.replace(temp_zip_path, comicPath + ".cbz")
#         return True

#     except Exception as e:
#         if os.path.exists(temp_zip_path):
#             os.remove(temp_zip_path)
#         return False
    
# def writeComicInfoData_zip(comicPath: str, data: ComicInfoData) -> bool:
#     """寫入漫畫資訊_壓縮檔

#     Args:
#         comicPath (str): 漫畫絕對路徑
#         data (ComicInfoData): 資料

#     Returns:
#         bool: 成功與否
#     """
#     temp_zip_path = comicPath + ".tmp"

#     try:
#         with zipfile.ZipFile(comicPath, 'r') as zin, zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_STORED) as zout:
#             original_path = data.get("original_path", "ComicInfo.xml")
#             # 寫入 ComicInfo.xml
#             zout.writestr(original_path, data2Xml(data))

#             for item in zin.infolist():
#                 if item.filename.lower().endswith("comicinfo.xml"):
#                     continue

#                 with zin.open(item) as f:
#                     zout.writestr(item.filename, f.read())

#         # 移除舊檔案，改名新檔案
#         if os.path.exists(comicPath):
#             os.remove(comicPath)
#         cbz_path = os.path.splitext(comicPath)[0] + ".cbz"
#         os.replace(temp_zip_path, cbz_path)
#         return True

#     except Exception as e:
#         if os.path.exists(temp_zip_path):
#             os.remove(temp_zip_path)
#         return False