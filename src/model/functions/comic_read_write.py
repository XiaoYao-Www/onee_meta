#####
# 漫畫檔案讀寫
#####
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
import zipfile
import shutil
from PySide6.QtGui import QPixmap
# 自訂庫
from src.classes.model.comic_data import ComicData, XmlComicInfo
from src.model.functions.uuid import newUUID4
from src.app_config import compressionComicExt, max_workers
from src.model.functions.comic_data_process import xml2Data, data2Xml
from src.logging_config import get_logger

_log = get_logger(__name__)


def readFirstImage(comicPath: str, imgExt: List[str]) -> QPixmap | None:
    """讀取第一章圖片

    Args:
        comicPath (str): 漫畫檔案路徑
        imgExt (List[str]): 圖片副檔名列表

    Returns:
        QPixmap | None: 第一章圖片
    """
    try:
        with zipfile.ZipFile(comicPath, 'r') as zf:
            first_path = next(
                (name for name in sorted(zf.namelist()) if name.lower().endswith(tuple(imgExt))),
                None
            )

            if first_path:
                # 2. 讀取該檔案的二進位內容 (bytes)
                with zf.open(first_path) as file:
                    img_data = file.read()
                
                # 3. 建立 QPixmap 並從資料中載入
                pixmap = QPixmap()
                # loadFromData 會自動偵測圖片格式
                if pixmap.loadFromData(img_data):
                    return pixmap
                    
        return None

    except Exception:
        _log.exception("讀取漫畫首圖失敗: %s", comicPath)
        return None

def countImage(comicPath: str, imgExt: List[str]) -> int:
    """計算漫畫圖片數量
    Args:
       comicPath (str): 漫畫檔案路徑
        imgExt (List[str]): 漫畫圖片副檔名列表
    
    Returns:
       int: 圖片數量
    """
    try:
        with zipfile.ZipFile(comicPath, 'r') as zf:
            number = 0
            for name in zf.namelist():
                if name.lower().endswith(tuple(imgExt)):
                    number += 1
            return number

    except Exception:
        _log.exception("計算漫畫圖片數量失敗: %s", comicPath)
        return 0

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

    except Exception:
        _log.exception("讀取壓縮檔 ComicInfo.xml 失敗: %s", comicPath)
        return None, {
            "nsmap": {},
            "fields": {},
        }

# ── 平行處理輔助型別 ──────────────────────────────────

@dataclass
class _ComicItem:
    """待處理的漫畫項目"""
    rel_path: str
    full_path: str
    is_compressed: bool


@dataclass
class _ComicResult:
    """單個漫畫處理結果（worker thread 產出，不含 QPixmap）"""
    rel_path: str
    comicInfo_path: Optional[str]
    xml_data: XmlComicInfo
    image_count: int
    first_image_bytes: Optional[bytes]


def _collect_comic_items(folderPath: str, imgExt: List[str], allowFile: List[str]) -> List[_ComicItem]:
    """掃描目錄，收集所有待處理的漫畫項目

    followlinks=False 防止循環符號連結。
    """
    items: List[_ComicItem] = []

    if not os.path.isdir(folderPath):
        return items

    for root, dirs, files in os.walk(folderPath, followlinks=False):
        folder_is_comic = True
        image_count = 0
        has_comicinfo = False

        if dirs:
            folder_is_comic = False

        for f in sorted(files):
            f_lower = f.lower()
            if f_lower.endswith(compressionComicExt):
                rel = os.path.relpath(os.path.join(root, f), folderPath)
                items.append(_ComicItem(
                    rel_path=rel,
                    full_path=os.path.join(folderPath, rel),
                    is_compressed=True,
                ))
                folder_is_comic = False
            elif f_lower.endswith(tuple(imgExt)):
                image_count += 1
            elif f_lower == "comicinfo.xml":
                has_comicinfo = True
            elif f in allowFile:
                pass
            else:
                folder_is_comic = False

        if folder_is_comic and image_count > 0:
            rel = os.path.relpath(root, folderPath)
            items.append(_ComicItem(
                rel_path=rel,
                full_path=os.path.join(folderPath, rel),
                is_compressed=False,
            ))

    return items


def _process_single_item(item: _ComicItem, folderPath: str, imgExt: List[str]) -> Optional[_ComicResult]:
    """在 worker thread 中處理單個漫畫項目

    不回傳 QPixmap，只回傳圖片位元組，由主執行緒建立 QPixmap。
    """
    try:
        if item.is_compressed:
            return _process_compressed(item, imgExt)
        else:
            return _process_folder(item, imgExt)
    except Exception:
        _log.exception("平行處理漫畫失敗: %s", item.rel_path)
        return None


def _process_compressed(item: _ComicItem, imgExt: List[str]) -> _ComicResult:
    """處理壓縮檔漫畫 (.zip / .cbz)"""
    original_path, xml_data = readZipXmlComicInfo(item.full_path)
    img_count = countImage(item.full_path, imgExt)
    img_bytes = _read_first_image_bytes(item.full_path, imgExt)
    return _ComicResult(
        rel_path=item.rel_path,
        comicInfo_path=original_path,
        xml_data=xml_data,
        image_count=img_count,
        first_image_bytes=img_bytes,
    )


def _process_folder(item: _ComicItem, imgExt: List[str]) -> _ComicResult:
    """處理資料夾漫畫"""
    comicinfo_path = os.path.join(item.full_path, "ComicInfo.xml")
    if os.path.isfile(comicinfo_path):
        with open(comicinfo_path, "rb") as f:
            xml_data = xml2Data(f.read())
    else:
        xml_data: XmlComicInfo = {"nsmap": {}, "fields": {}}

    img_count, first_img_bytes = _scan_folder_images(item.full_path, imgExt)
    return _ComicResult(
        rel_path=item.rel_path,
        comicInfo_path="ComicInfo.xml" if os.path.isfile(comicinfo_path) else None,
        xml_data=xml_data,
        image_count=img_count,
        first_image_bytes=first_img_bytes,
    )


def _read_first_image_bytes(comicPath: str, imgExt: List[str]) -> Optional[bytes]:
    """從壓縮檔讀取第一張圖片的位元組（thread-safe）"""
    try:
        with zipfile.ZipFile(comicPath, 'r') as zf:
            first_path = next(
                (name for name in sorted(zf.namelist()) if name.lower().endswith(tuple(imgExt))),
                None,
            )
            if first_path:
                with zf.open(first_path) as f:
                    return f.read()
        return None
    except Exception:
        _log.exception("讀取壓縮檔首圖位元組失敗: %s", comicPath)
        return None


def _scan_folder_images(folderPath: str, imgExt: List[str]) -> tuple[int, Optional[bytes]]:
    """掃描資料夾中的圖片"""
    count = 0
    first_bytes: Optional[bytes] = None
    img_lower = tuple(imgExt)
    try:
        for f in sorted(os.listdir(folderPath)):
            if f.lower().endswith(img_lower):
                count += 1
                if first_bytes is None:
                    full = os.path.join(folderPath, f)
                    with open(full, "rb") as fh:
                        first_bytes = fh.read()
    except Exception:
        _log.exception("掃描資料夾圖片失敗: %s", folderPath)
    return count, first_bytes


def readComicFolder(folderPath: str, imgExt: List[str], allowFile: List[str]) -> Dict[str, ComicData]:
    """讀取漫畫資料夾 — 使用 ThreadPoolExecutor 平行處理

    Args:
        folderPath: 資料夾路徑
        imgExt: 圖片副檔名列表
        allowFile: 允許的非圖片檔案

    Returns:
        Dict[str, ComicData]: uuid → 漫畫資料
    """
    if not os.path.isdir(folderPath):
        return {}

    # 1. 收集所有漫畫項目（主執行緒，快速）
    items = _collect_comic_items(folderPath, imgExt, allowFile)
    if not items:
        return {}

    # 2. 平行處理（worker threads）
    comic_data_cache: Dict[str, ComicData] = {}
    used_uuids: set[str] = set()
    workers = min(max_workers, len(items))
    _log.info("開始平行載入 %d 個漫畫項目 (%d workers)", len(items), workers)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(_process_single_item, item, folderPath, imgExt): item
            for item in items
        }
        for future in as_completed(future_to_item):
            result = future.result()
            if result is None:
                continue
            # 3. 組合 ComicData（主執行緒 — QPixmap 在此建立）
            new_uuid = newUUID4(used_uuids)
            used_uuids.add(new_uuid)

            first_image: Optional[QPixmap] = None
            if result.first_image_bytes:
                pixmap = QPixmap()
                if pixmap.loadFromData(result.first_image_bytes):
                    first_image = pixmap

            entry: ComicData = {
                "uuid": new_uuid,
                "comic_path": result.rel_path,
                "xml_comic_info": result.xml_data,
                "image_count": result.image_count,
                "first_image": first_image,
            }
            if result.comicInfo_path is not None:
                entry["comicInfo_path"] = result.comicInfo_path

            comic_data_cache[new_uuid] = entry

    _log.info("漫畫載入完成: %d 個項目", len(comic_data_cache))
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
        _log.exception("Error while creating CBZ from directory: %s", comicData.get("comic_path", "unknown"))
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
        _log.exception("Error while creating CBZ from zip: %s", comicData.get("comic_path", "unknown"))
        return False