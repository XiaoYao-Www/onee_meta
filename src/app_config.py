#####
# 開發設定
# 屬於硬編碼
#####

# app 設定檔路徑
appSettingJsonPath = "assets/app_setting.json"
# app icon
appIconPath = "assets/icon.png"
# 翻譯檔位置
translationFilePath = "assets/translations"
# 版本
appVersion = "1.2.6"
# 漫畫壓縮檔副檔名
compressionComicExt = (".zip", ".cbz")
# 平行處理工作執行緒數 (I/O 密集型，建議設為 CPU 核心數)
import os as _os
max_workers: int = _os.cpu_count() or 4
# info_editor_tab 配置已移轉至 src.view.tabs.info_editor_config
