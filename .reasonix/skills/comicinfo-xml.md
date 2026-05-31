---
name: comicinfo-xml
description: ComicInfo.xml 讀寫合併與佔位符 — XmlComicInfo TypedDict、xml2Data/data2Xml、updataXmlComicInfo、placeholder 系統
---

# ComicInfo.xml 元數據處理 — Onee Meta 專案

處理 ComicInfo.xml 的讀取、寫入、合併、佔位符替換。所有操作圍繞 `XmlComicInfo` TypedDict。

## 核心型別 — `src/classes/model/comic_data.py`

```python
class XmlComicInfo(TypedDict):
    nsmap: Dict[str, str]                    # namespace → URI
    fields: Dict[str, Dict[str, Union[str, None]]]  # namespace → {field: value}
```

`fields` 的頂層 key 是 namespace prefix（如 `"base"` 表示無 namespace 的欄位）。
常見 namespace：`"base"`（ComicInfo 標準欄位）、`"xsi"`（XML Schema Instance）。

## 解析與序列化 — `src/model/functions/comic_data_process.py`

```python
from src.model.functions.comic_data_process import xml2Data, data2Xml

# bytes → XmlComicInfo
data: XmlComicInfo = xml2Data(xml_bytes)

# XmlComicInfo → bytes（含 XML declaration, pretty_print）
xml_bytes: bytes = data2Xml(data)
```

## 欄位存取

```python
# 讀取 Title（base namespace, 無前綴）
title = data["fields"].get("base", {}).get("Title", "")

# 寫入欄位
data["fields"].setdefault("base", {})["Title"] = "新標題"

# 刪除欄位：設為空字串 ""
data["fields"]["base"]["Title"] = ""

# 讀取有 namespace 的欄位
manga = data["fields"].get("xsi", {}).get("Manga", "")
```

## 合併更新 — `src/controller/functions/xml_data_process.py`

```python
from src.controller.functions.xml_data_process import updataXmlComicInfo

# origin 會被就地修改
updataXmlComicInfo(origin, update)
"""
規則：
  - update 有但 origin 無 → 新增
  - update 值為非空字串 → 覆蓋
  - update 值為 "" → 刪除該欄位
  - update 未提及的欄位 → 保留不變
"""
```

## 常用 ComicInfo 欄位（base namespace）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `Title` | str | 漫畫標題 |
| `Series` | str | 系列名稱 |
| `Number` | str | 集數/話數 |
| `Count` | str | 總集數 |
| `Volume` | str | 卷數 |
| `Summary` | str | 簡介 |
| `Writer` | str | 作者 |
| `Publisher` | str | 出版社 |
| `Genre` | str | 類型 |
| `Tags` | str | 標籤（逗號分隔） |
| `LanguageISO` | str | 語言代碼 |
| `Year` | str | 年份 |
| `Month` | str | 月份 |
| `Day` | str | 日期 |
| `PageCount` | str | 頁數 |
| `Manga` | str | 是否為漫畫 ("Yes"/"No") |
| `Web` | str | 來源網址 |

新增欄位時，若 ComicRack 規範有定義的欄位應放在 `base` namespace。

## 佔位符系統 — `src/controller/functions/placeholder_process.py`

編輯器中可用佔位符（會自動替換為實際值）：

| 佔位符 | 說明 | 實作位置 |
|--------|------|---------|
| `{file_name}` | 檔名（不含副檔名） | ComicPlaceholderData.file_name |
| `{file_ext}` | 副檔名 | ComicPlaceholderData.file_ext |
| `{parent_folder}` | 父資料夾名稱 | ComicPlaceholderData.parent_folder |
| `{index}` | 全域索引（從 1 開始） | ComicPlaceholderData.index |
| `{order}` | 選取範圍內順序（從 1 開始） | ComicPlaceholderData.order |
| `{year}` | 當前年 | ComicPlaceholderData.year |
| `{month}` | 當前月（01-12） | ComicPlaceholderData.month |
| `{day}` | 當前日（01-31） | ComicPlaceholderData.day |
| `{date}` | YYYY-MM-DD | ComicPlaceholderData.date |
| `{clear_old_title}` | 原始 Title（去除 🔒 標記） | ComicPlaceholderData.clear_old_title |
| `{image_count}` | 圖片數量 | ComicPlaceholderData.image_count |

支援 Python Format String Syntax：`{index:03d}` → `005`, `{file_name:.5s}` → 前 5 字元。

## 新增 namespace / 欄位

若需新增非標準 namespace（如自訂擴充欄位）：

```python
# 1. 在 nsmap 宣告
data["nsmap"]["my_ns"] = "https://example.com/schema"

# 2. 寫入欄位
data["fields"].setdefault("my_ns", {})["CustomField"] = "value"
```

## DateTime 欄位注意事項

ComicInfo.xml 的 `Year`/`Month`/`Day` 是獨立欄位，非複合日期。
批次處理時應從檔名或資料夾推斷（見 `BatchProcessor._build_placeholder`）。
