# 環境定義
import sys
from pathlib import Path
## 動態添加 src 到模組路徑（以當前檔案位置為基準）
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = (BASE_DIR / "../../").resolve()
print(SRC_DIR)
sys.path.insert(0, str(SRC_DIR))

# 函式庫導入
from PySide6.QtCore import QCoreApplication
from types import MappingProxyType
## 自訂庫
from src.translations import TR
from src.classes.lazy_str import LazyStr

output_lines = [
    "from PySide6.QtCore import QCoreApplication",
    "",
    "# 給 pyside6-lupdate 用的，不會被實際執行",
    "if False:"
]

# 自動擷取所有 LazyStr 翻譯字串
for group_name in dir(TR):
    if group_name.startswith("_"):
        continue
    group = getattr(TR, group_name)
    if isinstance(group, MappingProxyType):
        for key, lazy in group.items():
            if isinstance(lazy, LazyStr):
                context = lazy.context
                text = lazy.text.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
                output_lines.append(f'    QCoreApplication.translate("{context}", "{text}")')

# 寫入檔案
with open("lupdate_stub_help.py", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("✅ lupdate_stub_help.py 已產生")
