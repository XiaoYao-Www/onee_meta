#####
# 漫畫檔案讀寫
#####
import os
from typing import List, Dict, Optional, Union
import zipfile
import shutil
# 自訂庫
from src.classes.model.comic_data import ComicData, XmlComicInfo
from src.model.functions.uuid import newUUID4
from src.app_config import compressionComicExt
from src.model.functions.comic_data_process import xml2Data, data2Xml


def readZipXmlComicInfo(comicPath: str) -> tuple[Union[str, None], XmlComicInfo]:
    """讀取封裝漫畫的資訊資料

    Args:
        comicPath (str): 漫畫檔案路徑

    Returns:
        tuple[str, XmlComicInfo]: [Xml路徑, Xml資料]
    """
    try:
        with zipfile.ZipFile(comicPath, 'r') as zf:
            # 取得第一個漫畫資訊檔案
            comicinfo_path = next(
                (name for name in zf.namelist() if name.lower().endswith("comicinfo.xml")),
                None
            )

            if not comicinfo_path:
                return None, {
                    "nsmap": {},
                    "fields": {},
                }

            with zf.open(comicinfo_path) as f:
                parsed = xml2Data(f.read())
                return comicinfo_path, parsed

    except Exception as e:
        return None, {
            "nsmap": {},
            "fields": {},
        }

def readComicFolder(folderPath: str, imgExt: List[str], allowFile: List[str]) -> Dict[str, ComicData]:
    """讀取漫畫資料夾

    Args:
        folderPath (str): 資料夾路徑
        imgExt (List[str]): 圖片附檔名
        allowFile (List[str]): 允許檔案

    Returns:
        Dict[str, ComicData]: 資料字典
    """
    comic_data_cache: Dict[str, ComicData] = {}

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
                original_path, xml_data = readZipXmlComicInfo(full_path)
                comic_data_cache[new_uuid4] = {
                    "uuid": new_uuid4,
                    "comic_path": rel_path,
                    "xml_comic_info": xml_data
                }
                if original_path != None:
                    comic_data_cache[new_uuid4]["comicInfo_path"] = original_path
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
                "comic_path": rel_path,
                "xml_comic_info": parsed,
            }

    return comic_data_cache

def writeComicData(rootPath: str, comicData: ComicData) -> bool:
    """寫入漫畫資料

    Args:
        rootPath (str): 根目錄
        comicData (ComicData): 漫畫資料

    Returns:
        bool: 成功與否
    """
    origin_path = os.path.join(rootPath, comicData["comic_path"])
    if os.path.isdir(origin_path):
        return writeComicData_dir(rootPath, comicData)
    elif os.path.isfile(origin_path) and origin_path.lower().endswith(compressionComicExt):
        return writeComicData_zip(rootPath, comicData)
    else:
        return False

def writeComicData_dir(rootPath: str, comicData: ComicData) -> bool:
    """寫入漫畫資訊_原資料夾
        (會更新輸入原資料)

    Args:
        rootPath (str): 跟路徑
        comicData (ComicData): 漫畫資料

    Returns:
        bool: 修改成功與否
    """
    origin_path = os.path.join(rootPath, comicData["comic_path"])
    temp_zip_path = os.path.join(rootPath, comicData["comic_path"] + ".tmp")
    output_cbz_path = os.path.join(rootPath, comicData["comic_path"] + ".cbz")

    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_STORED) as zout:
            # 先寫入 ComicInfo.xml
            zout.writestr("ComicInfo.xml", data2Xml(comicData["xml_comic_info"]))

            # 走訪整個資料夾結構
            for root, _, files in os.walk(origin_path):
                for file in files:
                    if file.lower() == "comicinfo.xml":
                        continue  # 跳過原本的 ComicInfo.xml

                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, origin_path)
                    zout.write(full_path, arcname=rel_path)

        # 成功後刪除原資料夾（確保路徑確實是資料夾）
        if os.path.isdir(origin_path):
            shutil.rmtree(origin_path)

        # 生成 CBZ
        os.replace(temp_zip_path, output_cbz_path)

        # 更新原資料
        comicData["comic_path"] += ".cbz"
        comicData["comicInfo_path"] = "ComicInfo.xml"

        return True

    except Exception as e:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        print(f"Error while creating CBZ: {e}")
        return False
    
def writeComicData_zip(rootPath: str, comicData: ComicData) -> bool:
    """寫入漫畫資訊_原壓縮檔
        (會更新輸入原資料)

    Args:
        rootPath (str): 跟路徑
        comicData (ComicData): 漫畫資料

    Returns:
        bool: 成功與否
    """
    original_path = os.path.join(rootPath, comicData["comic_path"])
    temp_zip_path = os.path.join(rootPath, comicData["comic_path"] + ".tmp")
    name, ext = os.path.splitext(comicData["comic_path"])
    output_cbz_path = os.path.join(rootPath, name + ".cbz")

    try:
        with zipfile.ZipFile(original_path, 'r') as zin, zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_STORED) as zout:
            original_comicinfo_path = comicData.get("comicInfo_path", "ComicInfo.xml")
            # 寫入 ComicInfo.xml
            zout.writestr(original_comicinfo_path, data2Xml(comicData["xml_comic_info"]))
        
            for item in zin.infolist():
                if item.filename.lower().endswith("comicinfo.xml"):
                    continue

                with zin.open(item) as f:
                    zout.writestr(item.filename, f.read())

        # 移除舊檔案
        if os.path.exists(original_path):
            os.remove(original_path)

        # 生成正式檔案
        os.replace(temp_zip_path, output_cbz_path)

        # 更新資料
        if not("comicInfo_path" in comicData):
            comicData["comicInfo_path"] = "ComicInfo.xml"
        comicData["comic_path"] = name + ".cbz"
        return True

    except Exception as e:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        return False