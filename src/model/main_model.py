#####
# 主model
#####
import json
from typing import Any, Optional, List, Dict, cast, Union
import os
from pathlib import Path
from natsort import natsorted
# 自訂庫
import src.app_config as APP_CONGIF
from src.classes.model.data_store import DataStore
from src.classes.model.comic_data import ComicData, XmlComicInfo
from src.model.functions.comic_read_write import readComicFolder, writeComicData
from src.classes.model.pyside_model.comic_list_model import ComicListModel

class MainModel():
    """主後端儲存
    """
    def __init__(self) -> None:
        # 資料讀取
        ## 應用設定
        old_setting = self.readAppSetting()
        ## 翻譯檔案
        translation_files = self.readLangFilesData()

        # 容器初始化
        ## 應用設定
        self.appSetting = DataStore()
        self.appSetting.update({
            "font_size": old_setting.get("font_size", 10), # 應用字體大小
            "lang": old_setting.get("lang", ""), # 語言 ("" 代表不使用翻譯)
            "image_exts": old_setting.get("image_exts", [ # 圖片附檔名
                ".jpg", ".jpeg", ".png",
                ".webp", ".bmp", ".gif",
            ]),
            "allow_files": old_setting.get("allow_files", [ # 允許檔案
                ".nomedia",
            ]),
        })
        ## 運行時資料儲存
        self.runningStore = DataStore()
        self.runningStore.update({
            "translation_files": translation_files, # 翻譯檔案字典
            "comic_folder_path": "", # 漫畫資料夾路徑
            "comic_uuid_list": [], # 漫畫UUID列表，用於ListView
            "selected_comics": [], # 選中的漫畫UUID
        })
        ## 漫畫資料儲存
        self.comicDataStore = DataStore()
        ## ListView Model
        self.comicListModel = ComicListModel(self.runningStore.get("comic_uuid_list"), self.comicDataStore)

        # 功能綁定
        self.appSetting.subscribe(self.saveAppSetting) # 綁定設定修改
    
    ##### 功能性函式

    ###### 漫畫列表排序

    def comicListSorted(self, type: int) -> None:
        """排序漫畫列表

        Args:
            type (int): 排序方式
        """
        # 取得基底名稱
        def get_basename_from_store(comic_uuid: str) -> str:
            data = cast(Union[ComicData, None], self.comicDataStore.get(comic_uuid))
            if not data:
                return ""
            path = data.get("comic_path")
            return Path(path).name
        # 取得集數
        def get_number_from_store(comic_uuid: str) -> int:
            data = cast(ComicData | None, self.comicDataStore.get(comic_uuid))
            if not data:
                return -1

            number = data.get("xml_comic_info", {}).get("fields", {}).get("base", {}).get("Number") or ""
            
            try:
                return int(number)
            except ValueError:
                return -1
        # 排序處理
        self.comicListModel.beginResetModel()
        try:
            uuid_list: list[str] = self.runningStore.get("comic_uuid_list", [])
            if type == 1:
                # natsorted 回傳新 list，所以要把排序結果覆蓋回原 list
                sorted_list: list[str] = natsorted(uuid_list, key=lambda u: get_basename_from_store(u))
                # 原地修改（保持引用）
                uuid_list[:] = sorted_list
            elif type == 2:
                uuid_list.sort(key=lambda x: get_number_from_store(x))
        finally:
            self.comicListModel.endResetModel()

    ###### 檔案讀寫

    def readComicFolder(self, comicFolderPath: str) -> None:
        """載入漫畫資料夾內容

        Args:
            comicFolderPath (str): 資料夾路徑(絕對)
        """
        # 設定漫畫資料夾路徑
        self.runningStore.set("comic_folder_path", comicFolderPath)
        # 讀取漫畫資料夾
        comic_editting_data: Dict[str, ComicData] = readComicFolder(
            comicFolderPath,
            self.appSetting.get("image_exts", []),
            self.appSetting.get("allow_files", []),
        )
        # 資料儲存
        self.comicDataStore.clear()
        self.comicDataStore.update(comic_editting_data)
        # 漫畫列表
        self.comicListModel.beginResetModel()
        self.runningStore.set("comic_uuid_list", list(comic_editting_data.keys())) # 創建新list
        self.comicListModel.uuidList = self.runningStore.get("comic_uuid_list", []) # 重新綁定list
        self.comicListModel.endResetModel()

    def writeComic(self, uuid: str) -> bool:
        """將漫畫資料寫入成檔案

        Args:
            uuid (str): UUID

        Returns:
            bool: 成功與否
        """
        rootPath:str = self.runningStore.get("comic_folder_path")
        comicData: ComicData = self.comicDataStore.get(uuid)
        return writeComicData(rootPath, comicData)

    ###### 應用設定檔

    def saveAppSetting(self, data: Dict[str, Any], id: Optional[str]) -> None:
        """儲存App設定到json

        Args:
            data (_type_): 設定
            id (_type_): 容器ID
        """
        with open(APP_CONGIF.appSettingJsonPath, "w", encoding="utf-8") as f:
            json.dump(self.appSetting.data, f, ensure_ascii=False, indent=4)

    def readAppSetting(self) -> Dict[str, Any]:
        """讀取之前的App設定

        Returns:
            dict[str, Any]: 設定值
        """
        # 檔案不存在，創建一個空的 JSON 檔
        if not os.path.exists(APP_CONGIF.appSettingJsonPath):
            with open(APP_CONGIF.appSettingJsonPath, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
            return {}
        
        with open(APP_CONGIF.appSettingJsonPath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # 如果檔案損壞，重置為空 JSON
                return {}
            
    ###### 翻譯檔
            
    def readLangFilesData(self) -> Dict[str, str]:
        """取得擁有的 .qm 翻譯檔案

        Returns:
            dict[str, str]: [翻譯檔名稱: 翻譯檔絕對路徑]
        """
        folder = Path(APP_CONGIF.translationFilePath)
        return { file.name.replace(".qm", ""): str(file.resolve()) for file in folder.glob("*.qm")}