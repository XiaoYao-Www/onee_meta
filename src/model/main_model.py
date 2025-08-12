import json
from typing import Any, Optional
import os
from pathlib import Path
# 自訂庫
from src.app_config import appSettingJsonPath, translationFilePath
from src.classes.data.data_store import DataStore

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
        })
        ## 應用資料儲存
        self.appStore = DataStore()
        self.appStore.update({
            "translation_files": translation_files, # 翻譯檔案字典
        })
        ## 漫畫資料儲存
        self.comicStore = DataStore()
        self.comicStore.update({

        })
        
        # 功能綁定
        self.appSetting.subscribe(self.saveAppSetting) # 綁定設定修改
    
    ##### 功能性函式

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