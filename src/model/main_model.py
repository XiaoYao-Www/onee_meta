import json
from typing import Any, Optional
import os
# 自訂庫
from src.app_config import appSettingJsonPath
from src.classes.data.data_store import DataStore

class MainModel():
    """主後端儲存
    """
    def __init__(self) -> None:
        # 儲存庫初始化
        ## 應用設定
        old_setting = self.readAppSetting()
        self.appSetting = DataStore()
        self.appSetting.update({
            "font_size": old_setting.get("font_size", 10), # 應用字體大小
        })
        ## 編輯器儲存
        self.editorStore = DataStore()
        self.editorStore.update({

        })
        
        # 功能綁定
        self.appSetting.subscribe(self.saveAppSetting) # 綁定設定修改
    
    ##### 功能性函式

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
