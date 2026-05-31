---
name: pyside-widget
description: 按 Onee Meta 專案規範建立 PySide6 元件 — Signal Bus、Catppuccin 主題、TR 翻譯、MVC 分層
---

# PySide6 Widget 建立規範 — Onee Meta 專案

當使用者要求新增/修改 PySide6 UI 元件時，嚴格遵循以下專案慣例。

## 架構分層 (MVC)

```
src/
├── model/        # 資料層：DataStore, TypedDict, 純邏輯（不得 import PySide6.QtWidgets）
├── view/         # UI 層：QWidget 子類別，.ui 檔案不存在，純程式碼建構
│   ├── widgets/  #   可復用元件（縮圖卡、載入對話框...）
│   └── tabs/     #   分頁內容
├── controller/   # 控制層：AsyncWorker, BatchProcessor, 訊號橋接
├── classes/      # 共享型別定義（TypedDict, dataclass）
└── common/       # 通用工具（純函式，無副作用）
```

**鐵律**：View 不直接操作 Model；透過 Controller 或 Signal Bus 傳遞。

## Signal Bus — 跨元件通訊

```python
from src.signal_bus import SIGNAL_BUS

# 發送端（View/Controller）
SIGNAL_BUS.uiSend.someAction.emit(payload)

# 接收端（在 MainView 或 Controller 中 connect）
SIGNAL_BUS.uiSend.someAction.connect(self.handler)
```

現有 Signal 清單（新增前先檢查是否可複用）：
- `uiSend.selectComicFolder(str)`, `uiSend.comicListSelected(list)`, `uiSend.startProcess()`
- `uiSend.comicListSort(int)`, `uiSend.fontSizeSet(int)`, `uiSend.langChange(str)`
- `uiRevice.translateUi()`, `uiRevice.sendCritical(str,str)`, `uiRevice.sendInformation(str,str)`
- `settingChange.fontSize(int)`

## 主題 — Apple 系暗色

**顏色 Token**（直接使用，不走變數）：
| Token | 用途 |
|-------|------|
| `#1c1c1e` | 全域背景 base |
| `#2c2c2e` | 元件背景 surface0，按鈕/輸入框 |
| `#3a3a3c` | hover 背景 surface1 |
| `#48484a` | pressed 背景 surface2 |
| `rgba(255,255,255,0.08)` | hairline 邊框 |
| `rgba(255,255,255,0.2)` | focus 邊框 |
| `#e5e5e5` | 主文字 text |
| `#8e8e93` | 次要文字 subtext0 |
| `#7c7c80` | 強調色 accent |
| `#636366` | 選中背景 selection |

**QSS 寫法**：
```python
self.setObjectName("myWidget")
self.setStyleSheet("""
    QWidget#myWidget {
        background: #2c2c2e;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        padding: 8px 12px;
    }
""")
```

## i18n 翻譯系統

```python
from src.translations import TR

# 模組級 key（對應 src/translations/<模組名>.py）
TR.MY_MODULE["原始文字"]()
# 注意：TR 物件屬性名對應翻譯模組檔案名（不含 .py）
```

新增翻譯時，在 `src/translations/` 下建立對應模組，並在 `_aggregator.py` 註冊。

## Widget 樣板

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from src.signal_bus import SIGNAL_BUS
from src.translations import TR

class MyNewWidget(QWidget):
    """新元件 — 簡述用途"""

    # 自訂 Signal（如需）
    dataReady = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.signal_connection()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        # ... 建立子元件 ...

    def signal_connection(self):
        """集中管理所有 Signal 連線"""
        SIGNAL_BUS.settingChange.fontSize.connect(self.changeFontSize)

    def changeFontSize(self, size: int):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def retranslateUi(self):
        """翻譯更新時呼叫"""
        pass
```

## 非同步操作

耗時操作（I/O、XML 解析）必須透過 `AsyncWorker`，禁止在主執行緒執行：

```python
from src.controller.async_worker import run_async

def heavy_work(data):
    # 在背景執行緒執行
    return result

def on_done(result):
    # 回到主執行緒更新 UI
    self.label.setText(str(result))

thread, worker = run_async(heavy_work, on_result=on_done)
# 保存 thread/worker 引用防止 GC
self._thread = thread
self._worker = worker
```

## 字體大小

所有 Widget 需支援 `changeFontSize(int)`，從 Signal Bus 接收：
```python
SIGNAL_BUS.settingChange.fontSize.connect(self.changeFontSize)
```

## 命名慣例

- Widget 類別：`CamelCase`
- 方法/變數：`snake_case`
- 私有方法：`_prefix`
- Object name（QSS 選擇器）：`camelCase`
- Layout 變數：`xxx_layout`（如 `main_layout`, `button_layout`）
