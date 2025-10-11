import json
from typing import Any, Optional, List, Dict
import os
from pathlib import Path
# 自訂庫
from src.app_config import appSettingJsonPath, translationFilePath
from src.classes.data.data_store import DataStore
from src.classes.data.comic_info_data import ComicInfoData
from src.model.functions.comic_read_write import readComicFolder

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
        ## 應用資料儲存
        self.appStore = DataStore()
        self.appStore.update({
            "translation_files": translation_files, # 翻譯檔案字典
            "comic_folder_path": "", # 漫畫資料夾路徑
            "comic_list": [], # 漫畫列表，用於顯示排序
            "comic_select": {}, # 儲存選中的漫畫
        })
        ## 漫畫資料儲存
        self.comicStore = DataStore()
        
        # 功能綁定
        self.appSetting.subscribe(self.saveAppSetting) # 綁定設定修改
    
    ##### 功能性函式

    ###### 檔案讀寫

    def readComicFolder(self, comicFolderPath: str) -> None:
        """載入漫畫資料夾內容

        Args:
            comicFolderPath (str): 資料夾路徑
        """
        comic_editting_data: Dict[str, ComicInfoData] = readComicFolder(
            comicFolderPath,
            self.appSetting.get("image_exts", []),
            self.appSetting.get("allow_files", []),
        )
        # 資料儲存
        self.comicStore.clear()
        self.comicStore.update(comic_editting_data)
        # 漫畫列表
        self.appStore.set("comic_list", list(comic_metadata.keys()))

    ###### 應用設定檔

    def saveAppSetting(self, data: dict[str, Any], id: Optional[str]) -> None:
        """儲存App設定到json

        Args:
            data (_type_): 設定
            id (_type_): 容器ID
        """
        with open(appSettingJsonPath, "w", encoding="utf-8") as f:
            json.dump(self.appSetting.data, f, ensure_ascii=False, indent=4)

    def readAppSetting(self) -> dict[str, Any]:
        """讀取之前的App設定

        Returns:
            dict[str, Any]: 設定值
        """
        # 檔案不存在，創建一個空的 JSON 檔
        if not os.path.exists(appSettingJsonPath):
            with open(appSettingJsonPath, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
            return {}
        
        with open(appSettingJsonPath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # 如果檔案損壞，重置為空 JSON
                return {}
            
    ###### 翻譯檔
            
    def readLangFilesData(self) -> dict[str, str]:
        """取得擁有的 .qm 翻譯檔案

        Returns:
            dict[str, str]: [翻譯檔名稱: 翻譯檔絕對路徑]
        """
        folder = Path(translationFilePath)
        return { file.name.replace(".qm", ""): str(file.resolve()) for file in folder.glob("*.qm")}