---
name: batch-process
description: 批次處理與非同步模式 — AsyncWorker、BatchProcessor、DataStore、ThreadPoolExecutor、備份還原
---

# 批次處理與非同步任務 — Onee Meta 專案

新增批次處理功能或非同步任務時，遵循以下模式。

## AsyncWorker — 非同步執行引擎

檔案：`src/controller/async_worker.py`

所有耗時操作（I/O、XML 解析、圖片處理）必須透過 AsyncWorker 在 QThread 中執行，防止 UI 凍結。

```python
from src.controller.async_worker import run_async

def heavy_task(param1, param2):
    """在背景執行緒執行 — 不得操作 QWidget/QPixmap"""
    # 可做：檔案 I/O、XML 解析、bytes 處理
    result = do_something(param1, param2)
    return result

def on_result(result):
    """回到主執行緒 — 可安全操作 UI"""
    self.label.setText(str(result))

def on_error(msg: str):
    """主執行緒錯誤處理"""
    QMessageBox.critical(self, "錯誤", msg)

def on_progress(msg: str, current: int, max_: int):
    """主執行緒進度回報"""
    self.progress_bar.setMaximum(max_)
    self.progress_bar.setValue(current)

# 啟動
thread, worker = run_async(
    heavy_task,
    on_result=on_result,
    on_error=on_error,
    on_progress=on_progress,
    on_finished=lambda: self.setStatus("完成"),
)

# 保存引用！防止被 GC 吃掉
self._active_thread = thread
self._active_worker = worker
```

### WorkerSignals 可用訊號

| Signal | 參數 | 說明 |
|--------|------|------|
| `started` | 無 | 任務開始 |
| `progress` | (str, int, int) | 訊息、當前進度、最大值 |
| `result` | object | 回傳值 |
| `error` | str | 錯誤訊息 |
| `finished` | 無 | 無論成敗都會觸發 |

### 如何在 worker 中回報進度

```python
def heavy_task():
    # 透過 closure 或 partial 傳入 worker 實例
    for i, item in enumerate(items):
        process(item)
        # worker.signals.progress.emit(f"處理中...", i+1, len(items))
    return result
```

更完整做法：讓 `fn` 接受 `signals` 參數，或使用 partial：

```python
from functools import partial

def heavy_task(signals, data):
    for i, item in enumerate(data):
        process(item)
        signals.progress.emit(f"處理 {item}", i+1, len(data))
    return "done"

fn = partial(heavy_task, signals=worker.signals, data=mydata)
```

## BatchProcessor — 批次寫入模式

檔案：`src/controller/batch_processor.py`

```python
class BatchProcessor:
    def __init__(self, comic_data_store, running_store, write_comic_fn):
        ...

    def process(self, editor_data: XmlComicInfo) -> BatchResult:
        """核心流程：
        1. 從 running_store 取得選取的 uuid 列表
        2. 遍歷每個 uuid：
           a. 建立 ComicPlaceholderData
           b. XmlDataPlaceholderProcess 替換佔位符
           c. 備份原始 xml_comic_info（deepcopy）
           d. updataXmlComicInfo 合併
           e. write_comic_fn 寫入
           f. 失敗則還原備份
        3. 回傳 BatchResult(success, fail, total)
        """
```

### BatchResult

```python
class BatchResult:
    success: int   # 成功數
    fail: int      # 失敗數
    total: int     # 總數
    all_success: bool  # 是否全部成功（fail == 0）
```

### 擴充 BatchProcessor

新增處理步驟時，在 `process()` 迴圈中加入：

1. **先備份**：`backup = copy.deepcopy(original)`
2. **再修改**：對 `original` 進行變更
3. **寫入檢查**：呼叫 `self._write_comic(uuid)`
4. **失敗還原**：`comic_data["key"] = backup`

```python
# 新增處理範例（在 _build_placeholder 之後）
# 備份
old_tags = comic_data.get("xml_comic_info", {}).get("fields", {}).get("base", {}).get("Tags", "")
backup_tags = old_tags

# 修改
if "base" not in processed["fields"]:
    processed["fields"]["base"] = {}
processed["fields"]["base"]["Tags"] = new_tags_value

# 寫入 + 還原（由現有流程處理）
```

## DataStore — 執行階段資料儲存

檔案：`src/classes/model/data_store.py`

```python
# 設定值
store.set("key", value)

# 讀取值
value = store.get("key")            # 或 None
value = store.get("key", default)

# 批次更新
store.update({"k1": v1, "k2": v2})

# 訂閱變更（變更時自動回調）
handle = store.subscribe(callback)  # callback(changes: dict, store_id: str | None)

# 取消訂閱
store.unsubscribe(handle)
```

專案中兩個主要 DataStore：
- `comic_data_store`：uuid → ComicData（漫畫資料）
- `running_store`：執行階段狀態（selected_comics, comic_uuid_list, active_folder...）

## 平行處理 — ThreadPoolExecutor

大量獨立 I/O 操作使用 `ThreadPoolExecutor`（見 `readComicFolder`）：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.app_config import max_workers

workers = min(max_workers, len(items))

with ThreadPoolExecutor(max_workers=workers) as executor:
    future_to_item = {
        executor.submit(process_fn, item): item
        for item in items
    }
    for future in as_completed(future_to_item):
        result = future.result()
        if result is not None:
            handle(result)
```

**規則**：
- Worker function 內不得建立 QPixmap（回傳 bytes 即可）
- 回主執行緒後再建立 QPixmap
- 例外在 worker 內捕捉，回傳 None 表示跳過

## 新增功能的檢查清單

- [ ] 耗時操作 → AsyncWorker，不在主執行緒
- [ ] 大量 I/O → ThreadPoolExecutor，上限 `max_workers`
- [ ] 修改前 → `copy.deepcopy` 備份
- [ ] 寫入失敗 → 還原備份
- [ ] 所有例外 → try/except + log
- [ ] 進度回報 → signals.progress.emit
- [ ] worker/QThread 引用 → 保存在 `self` 防止 GC
