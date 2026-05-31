---
name: cbz-archive
description: CBZ/ZIP 漫畫封裝檔讀寫 — readComicFolder、writeComicData、封面提取、圖片計數、資料夾轉 CBZ
---

# CBZ/ZIP 漫畫封裝檔操作 — Onee Meta 專案

處理 CBZ（其實就是 ZIP）漫畫檔案的讀取、寫入、封面提取、圖片計數、格式轉換。

## 核心概念

- CBZ 檔本質是 ZIP 檔（通常使用 `ZIP_STORED` 無壓縮）
- 支援的副檔名定義在 `src/app_config.py` → `compressionComicExt`（`.cbz`, `.zip`）
- 支援兩種漫畫形式：**壓縮檔**（.cbz/.zip）和**資料夾**（內含圖片）
- ComicInfo.xml 在壓縮檔/資料夾的根層級

## 讀取操作 — `src/model/functions/comic_read_write.py`

```python
from src.model.functions.comic_read_write import (
    readFirstImage,        # 讀取第一張圖 → QPixmap | None
    countImage,            # 計算圖片數量 → int
    readZipXmlComicInfo,   # 讀取 ComicInfo.xml → (路徑|None, XmlComicInfo)
    readComicFolder,       # 掃描整個目錄 → Dict[uuid, ComicData]（平行處理）
)

# 讀取第一張封面圖（用於縮圖顯示）
pixmap: QPixmap | None = readFirstImage("path/to/comic.cbz", imgExt=[".jpg", ".png"])

# 計算漫畫頁數
pages: int = countImage("path/to/comic.cbz", imgExt=[".jpg", ".png"])

# 讀取 ComicInfo.xml
comicinfo_path, xml_data = readZipXmlComicInfo("path/to/comic.cbz")
# comicinfo_path 可能是 "ComicInfo.xml" 或 None（不存在）

# 掃描整個收藏庫（使用 ThreadPoolExecutor 平行處理，max_workers 在 app_config）
all_comics: Dict[str, ComicData] = readComicFolder(
    folderPath="/home/user/comics",
    imgExt=[".jpg", ".png", ".webp"],
    allowFile=["info.txt", ".gitkeep"],
)
```

## 寫入操作

```python
from src.model.functions.comic_read_write import (
    writeComicData,          # 自動判斷類型分派
    writeComicData_dir,      # 資料夾 → CBZ（含轉換）
    writeComicData_zip,      # ZIP → CBZ（原地更新 ComicInfo.xml）
)

# writeComicData 自動判斷路徑是資料夾還是壓縮檔，分派到對應處理
success: bool = writeComicData(rootPath="/home/user/comics", comicData=comic_data)
```

### 資料夾 → CBZ 轉換流程 (`writeComicData_dir`)

1. 建立 `xxx.tmp` 暫存 ZIP
2. 先寫入 `ComicInfo.xml`（確保在壓縮檔根部）
3. 走訪整個資料夾，跳過原有的 `ComicInfo.xml`
4. 寫入所有其他檔案（保留原始目錄結構）
5. 刪除原始資料夾
6. 將 `.tmp` rename 為 `.cbz`
7. 更新 `comicData["comic_path"]` 和 `comicData["comicInfo_path"]`

### ZIP → CBZ 更新流程 (`writeComicData_zip`)

1. 建立 `xxx.tmp` 暫存 ZIP
2. 先寫入新的 `ComicInfo.xml`
3. 複製原始 ZIP 中所有非 ComicInfo.xml 的檔案
4. 刪除原始檔案
5. 將 `.tmp` rename 為 `.cbz`
6. 更新 `comicData["comic_path"]`

**注意**：無論原始是 `.zip` 還是 `.cbz`，輸出統一是 `.cbz`。

## 圖片讀取（thread-safe）

在 Worker Thread 中讀取圖片時，需回傳 **bytes** 而非 QPixmap（QPixmap 只能在主執行緒建立）：

```python
from src.model.functions.comic_read_write import _read_first_image_bytes

# Worker thread 中
img_bytes: bytes | None = _read_first_image_bytes("path/to/comic.cbz", [".jpg", ".png"])

# 回到主執行緒後
pixmap = QPixmap()
pixmap.loadFromData(img_bytes)
```

## 平行掃描 — `readComicFolder` 內部架構

```
_collect_comic_items()     → 主執行緒，快速收集檔案列表
_executor.submit() × N     → 每個漫畫在獨立 Thread 處理
  ├─ _process_compressed() → .cbz/.zip（讀 ComicInfo + 計數 + 首圖 bytes）
  └─ _process_folder()     → 資料夾（讀 ComicInfo + 掃描圖片）
組合 ComicData              → 主執行緒（bytes → QPixmap）
```

`max_workers` 來自 `src/app_config.py`，預設值為 32。

## 新增功能時的注意事項

- 所有 ZIP 操作使用 `zipfile.ZipFile`，不使用外部命令
- 寫入時用 `ZIP_STORED`（無壓縮），保持與其他閱讀器相容
- 錯誤時需清理 `.tmp` 暫存檔（見 `writeComicData_dir` 的 finally 區塊）
- 所有 I/O 操作需包在 try/except 中並記錄 log
- 大量檔案操作應使用 `ThreadPoolExecutor` 避免 UI 凍結
