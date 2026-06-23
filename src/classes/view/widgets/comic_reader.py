"""
內建漫畫閱讀器 — 支援單頁 / 雙頁 / 滾動三種閱讀模式

架構總覽
--------
- 三種閱讀模式：SINGLE（單頁 fit-width）、DOUBLE（雙頁並排）、SCROLL（縱向連續滾動）。
- 非同步圖片載入管線：worker thread 讀取圖片 bytes (IO bound) →
  主執行緒 _bytes_to_pixmap 轉換 QPixmap (GUI bound)，避免阻塞 UI。
- LRU 圖片快取 _ImageCache：以 page index 為鍵，保留最近存入的 max_size 張。
- 滾動模式使用前綴和偏移表 (prefix-sum offset table) 追蹤每頁垂直位置；
  初始以估計高度填滿，載入後更新為真實值，scroll 事件 debounce 後觸發載入/卸載。

用法:
    from src.classes.view.widgets.comic_reader import ComicReaderWidget

    reader = ComicReaderWidget(comic_full_path)
    reader.exec()
"""
import os
import bisect
import zipfile
from enum import Enum, auto
from typing import List, Optional, Dict, Callable, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QKeyEvent, QPainter, QColor

from src.controller.async_worker import run_async
from src.app_config import compressionComicExt
from src.logging_config import get_logger

_log = get_logger(__name__)

# ── 支援圖片格式 ──────────────────────────────────────
_DEFAULT_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")

# ── 閱讀模式 ──────────────────────────────────────────
class ReadingMode(Enum):
    SINGLE = auto()   # 單頁，fit-width
    DOUBLE = auto()   # 雙頁並排
    SCROLL = auto()   # 縱向連續滾動


class _ImageCache:
    """LRU 圖片快取

    以 page index (int) 為鍵，QPixmap 為值的字典。
    淘汰策略：當超過 max_size 時移除 key 最小者
    ── 由於 page index 單調遞增，min(key) 實際等同 FIFO/LRU。

    注意：QPixmap 只能在建立它的 thread （主執行緒）上使用，
    因此本類別所有操作都發生在主執行緒。
    """

    def __init__(self, max_size: int = 20) -> None:
        """
        :param max_size: 最多保留的頁面數量，超過時淘汰最舊頁面
        :type max_size: int
        """
        self._max = max_size
        self._data: Dict[int, QPixmap] = {}

    def get(self, page: int) -> Optional[QPixmap]:
        """
        :param page: 頁碼 (0-based)
        :return: 快取中的 QPixmap，若不存在則回傳 None
        """
        return self._data.get(page)

    def put(self, page: int, pixmap: QPixmap) -> None:
        """
        存入頁面 pixmap，若超過上限則淘汰最舊頁面。

        :param page: 頁碼 (0-based)
        :param pixmap: 要快取的 QPixmap
        """
        self._data[page] = pixmap
        if len(self._data) > self._max:
            oldest = min(self._data.keys())
            del self._data[oldest]

    def evict_outside(self, keep: set) -> None:
        """
        保留指定頁碼集合，移除其餘所有快取項目。

        :param keep: 要保留的頁碼集合 (set of int)
        """
        for k in list(self._data.keys()):
            if k not in keep:
                del self._data[k]

    def clear(self) -> None:
        """清空所有快取"""
        self._data.clear()


# ── 非同步圖片載入 ────────────────────────────────────
def _load_image_bytes(comic_path: str, is_compressed: bool,
                      filename: str) -> Optional[bytes]:
    """在 worker thread 中讀取單張圖片，回傳 bytes

    此函式應在 worker thread 中執行，不涉及任何 Qt 物件，
    因此可安全地在非主執行緒中呼叫。

    :param comic_path: 漫畫資料夾路徑（非壓縮）或壓縮檔路徑（壓縮）
    :param is_compressed: 是否為 zip/cbz 壓縮檔
    :param filename: 目標圖片檔名（相對於 comic_path）
    :return: 圖片的原始 bytes，讀取失敗則回傳 None
    :rtype: Optional[bytes]
    """
    try:
        if is_compressed:
            with zipfile.ZipFile(comic_path, "r") as zf:
                with zf.open(filename) as f:
                    return f.read()
        else:
            full = os.path.join(comic_path, filename)
            with open(full, "rb") as f:
                return f.read()
    except Exception:
        _log.exception("讀取圖片失敗: %s", filename)
        return None


def _bytes_to_pixmap(data: Optional[bytes]) -> Optional[QPixmap]:
    """bytes → QPixmap

    必須在主執行緒（GUI thread）中呼叫，因為 QPixmap 的建立需要
    QApplication 實例與 OpenGL context（視平台而定），
    跨 thread 使用會導致崩潰。

    :param data: 圖片原始 bytes（由 _load_image_bytes 取得）
    :return: QPixmap，若 data 為 None 或解析失敗則回傳 None
    :rtype: Optional[QPixmap]
    """
    if data is None:
        return None
    p = QPixmap()
    if p.loadFromData(data):
        return p
    return None


# ═══════════════════════════════════════════════════════
# 閱讀器
# ═══════════════════════════════════════════════════════
class ComicReaderWidget(QDialog):
    """內建漫畫閱讀器 — 三種閱讀模式

    架構特性
    --------
    - 支援壓縮檔 (zip/cbz) 與資料夾兩種漫畫來源，透過 compressionComicExt 判斷。
    - 三種閱讀模式各自有獨立的顯示元件：_PageView（SINGLE/DOUBLE）或
      動態 QLabel 串（SCROLL），由 _switch_mode 切換。
    - 非同步載入管線：_async() 啟動 worker thread → _load_image_bytes (IO) →
      _bytes_to_pixmap (主執行緒) → 寫入 _ImageCache。
    - 滾動模式採用「前綴和偏移表」（_page_offsets）追蹤每頁 Y 位置，
      初始以估計高度填充，載入後校正為真實值；scroll 事件經 30ms debounce
      後觸發可視範圍載入與遠端卸載。
    - 關閉時設 _closing 旗標使所有進行中的 callback 變成 no-op，
      避免 thread 回呼存取已銷毀的 Qt 物件。
    """

    WIDTH = 1000
    HEIGHT = 720

    def __init__(self, comic_full_path: str, parent=None) -> None:
        """
        :param comic_full_path: 漫畫資料夾路徑或壓縮檔 (.zip/.cbz) 路徑
        :param parent: 父視窗 (QWidget)
        """
        super().__init__(parent)
        self._comic_path = comic_full_path
        # 根據副檔名判斷是否為壓縮檔（比對 compressionComicExt 中的合法副檔名）
        self._is_compressed = comic_full_path.lower().endswith(compressionComicExt)

        # ── 狀態 ──
        self._image_files: List[str] = []      # 排序後的圖片檔名列表
        self._current_page: int = 0            # 目前頁碼 (0-based)
        self._total_pages: int = 0             # 總頁數
        self._mode: ReadingMode = ReadingMode.SINGLE  # 目前閱讀模式
        self._closing: bool = False            # 關閉旗標，設為 True 後所有回呼跳過
        self._cache = _ImageCache(max_size=30) # 主快取，SINGLE/DOUBLE/SCROLL 共用
        self._workers: List[Tuple] = []        # ← 必須追蹤 thread 引用，否則 GC 會回收正在執行的 QThread

        self._load_file_list()

        # ── 視窗 ──
        self.setWindowTitle(self._window_title())
        self.resize(self.WIDTH, self.HEIGHT)
        self.setMinimumSize(500, 360)

        # ── 佈局 ──
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._build_toolbar(self._main_layout)

        # 顯示元件（根據模式切換）
        self._display_widget: Optional[QWidget] = None
        self._switch_mode(ReadingMode.SINGLE, self._main_layout)

        # 延遲 50ms 觸發首次頁面載入，讓事件迴圈先完成初始 paint
        # 否則視窗尚未佈局完成，QPixmap 縮放可能使用錯誤的尺寸
        QTimer.singleShot(50, lambda: self._show_page(0))

    # ── 檔案掃描 ──────────────────────────────────────

    def _load_file_list(self) -> None:
        """掃描漫畫來源，建立排序後的圖片檔名列表

        過濾規則：
        - 只保留 _DEFAULT_IMG_EXT 中定義的副檔名 (.jpg/.jpeg/.png/.webp/.gif/.bmp)
        - 排除 macOS 的 __MACOSX 目錄下的檔案
        - 排除以點號開頭的隱藏檔案（如 .DS_Store）
        - 使用 sorted() 確保分頁順序與檔名排序一致（自然排序，無自然數處理）
        """
        try:
            if self._is_compressed:
                with zipfile.ZipFile(self._comic_path, "r") as zf:
                    all_names = zf.namelist()
                self._image_files = sorted(
                    n for n in all_names
                    if n.lower().endswith(_DEFAULT_IMG_EXT)
                       and not n.startswith("__MACOSX")
                       and not n.startswith(".")
                )
            else:
                all_names = os.listdir(self._comic_path)
                self._image_files = sorted(
                    n for n in all_names
                    if n.lower().endswith(_DEFAULT_IMG_EXT)
                )
        except Exception:
            _log.exception("讀取漫畫檔案列表失敗: %s", self._comic_path)
        self._total_pages = len(self._image_files)

    # ── 非同步 worker 管理 ────────────────────────────

    def _async(self, fn: Callable, on_result: Callable) -> None:
        """啟動非同步載入並追蹤 thread 引用防止 GC

        Python 的 GC 會回收未被引用的 QThread 物件，即使 thread 仍在執行。
        為避免此問題，將 (thread, worker) 存入 self._workers 列表，
        當 worker 發出 finished 信號時再將該 entry 從列表中移除。

        資料流：
            fn 在 worker thread 中執行（通常是 _load_image_bytes）
            → 回傳值傳給 on_result 在主執行緒執行（通常是 _bytes_to_pixmap + cache.put）

        :param fn: 在 worker thread 中執行的零引數函式，回傳 Optional[bytes]
        :param on_result: 在主執行緒執行的回呼，接收 fn 的回傳值
        """
        if self._closing:
            return
        t, w = run_async(fn, on_result=on_result)
        entry = (t, w)
        self._workers.append(entry)

        def _cleanup():
            if entry in self._workers:
                self._workers.remove(entry)

        # 用 worker 的 finished（工作做完 thread 將退出時觸發）
        # cleanup 只移除 Python 引用，不碰 C++ thread
        w.signals.finished.connect(_cleanup)

    # ── UI 建構 ──────────────────────────────────────

    def _build_toolbar(self, parent_layout: QVBoxLayout) -> None:
        """建置頂部工具列

        佈局 (水平排列)：
            [單頁] [雙頁] [滾動] —— stretch —— [◀ 上一頁] [下一頁 ▶] —— stretch —— [頁碼] [關閉]

        注意 lambda 閉包：lambda checked=False, m=mode: self._on_mode_click(m)
        中的 m=mode 透過預設引數綁定 mode 的目前值 (by value)，
        避免延遲求值 (late-binding) 導致所有按鈕都指向最後一個 mode。
        """
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setObjectName("readerToolbar")
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(12, 4, 12, 4)
        row.setSpacing(8)

        # ── 閱讀模式分段控制 ──
        self._mode_btns: Dict[ReadingMode, QPushButton] = {}
        for mode, label in [(ReadingMode.SINGLE, "單頁"),
                            (ReadingMode.DOUBLE, "雙頁"),
                            (ReadingMode.SCROLL, "滾動")]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setFixedWidth(68)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._mode_btn_css(False))
            btn.clicked.connect(lambda checked=False, m=mode: self._on_mode_click(m))
            self._mode_btns[mode] = btn
            row.addWidget(btn)
        self._refresh_mode_style()

        row.addStretch(2)

        # ── 導航按鈕 ──
        self._prev_btn = QPushButton("◀  上一頁")
        self._prev_btn.setFixedHeight(28)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._go_prev)
        self._next_btn = QPushButton("下一頁  ▶")
        self._next_btn.setFixedHeight(28)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._next_btn.clicked.connect(self._go_next)
        row.addWidget(self._prev_btn)
        row.addWidget(self._next_btn)

        row.addStretch(1)

        # ── 頁碼 + 關閉 ──
        self._page_label = QLabel("— / —")
        self._page_label.setStyleSheet("color: #8e8e93; font-size: 13px;")

        close_btn = QPushButton("關閉")
        close_btn.setFixedHeight(28)
        close_btn.setMinimumWidth(64)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)

        row.addWidget(self._page_label)
        row.addSpacing(8)
        row.addWidget(close_btn)

        parent_layout.addWidget(toolbar)

    @staticmethod
    def _mode_btn_css(active: bool) -> str:
        """回傳模式按鈕的 CSS

        :param active: True 表示目前激活的模式，使用深色底白字；
                       False 表示非激活模式，使用透明底灰字，hover 時漸亮
        :return: Qt stylesheet 字串
        """
        if active:
            return ("QPushButton { background: #636366; color: #fff;"
                    " border: none; border-radius: 5px; }")
        return ("QPushButton { background: transparent; color: #8e8e93;"
                " border: none; border-radius: 5px; }"
                "QPushButton:hover { background: rgba(255,255,255,0.08);"
                " color: #e5e5e5; }")

    def _refresh_mode_style(self) -> None:
        """根據目前 self._mode 重新整理所有模式按鈕的樣式"""
        for m, btn in self._mode_btns.items():
            btn.setStyleSheet(self._mode_btn_css(m == self._mode))

    def _window_title(self) -> str:
        """產生視窗標題，含目前頁碼 / 總頁數"""
        base = os.path.basename(self._comic_path)
        if self._total_pages == 0:
            return f"Reader — {base}"
        return f"Reader — {base}  ({self._current_page+1}/{self._total_pages})"

    def _on_mode_click(self, mode: ReadingMode) -> None:
        """模式按鈕點擊處理：切換模式並維持目前頁碼"""
        if mode == self._mode:
            return
        self._switch_mode(mode, self._main_layout)
        self._show_page(self._current_page)

    # ── 模式切換 ──────────────────────────────────────

    def _switch_mode(self, mode: ReadingMode,
                     layout: Optional[QVBoxLayout] = None) -> None:
        """切換閱讀模式，重建顯示元件

        元件生命週期：
        1. 從 layout 中移除舊元件 (removeWidget)
        2. 呼叫 deleteLater() — Qt 在下一事件迴圈迭代時才真正銷毀 C++ 物件，
           確保所有 pending signal/slot 安全解除
        3. 依據新模式建立 _PageView（SINGLE/DOUBLE）或滾動容器（SCROLL）
        4. 加入 layout

        :param mode: 目標閱讀模式
        :param layout: 父 layout，預設為 self._main_layout
        """
        layout = layout or self._main_layout
        if layout is None:
            return

        self._mode = mode
        self._refresh_mode_style()

        # 移除舊顯示元件
        if self._display_widget is not None:
            # 若從 SCROLL 模式離開，先切斷 debounce timer 防止 callback
            # 在 deleteLater() 之後存取已銷毀的 scroll 物件
            if self._mode == ReadingMode.SCROLL:
                if hasattr(self, '_scroll_debounce'):
                    try:
                        self._scroll_debounce.timeout.disconnect()
                    except (TypeError, RuntimeError):
                        pass
                    self._scroll_debounce.stop()
                # 清空滾動相關屬性，防止過期 callback 存取已銷毀物件
                # （這些屬性只存在於 SCROLL 模式中，由 _build_scroll 建立）
                self._scroll_area = None
                self._scroll_labels = []
                self._page_heights = []
                self._page_offsets = [0]
                if hasattr(self, '_scroll_loading'):
                    self._scroll_loading.clear()
            layout.removeWidget(self._display_widget)
            self._display_widget.deleteLater()
            self._display_widget = None

        # 建立新顯示元件
        if mode == ReadingMode.SCROLL:
            self._display_widget = self._build_scroll()
        else:
            self._display_widget = _PageView(self, mode)

        layout.addWidget(self._display_widget, stretch=1)

        # 滾動模式隱藏翻頁按鈕（滾動模式靠 scrollbar / 鍵盤翻頁）
        is_scroll = (mode == ReadingMode.SCROLL)
        self._prev_btn.setVisible(not is_scroll)
        self._next_btn.setVisible(not is_scroll)

    # ── 滾動模式 ──────────────────────────────────────

    _SCROLL_BUFFER = 4          # 可視區域上下各預載頁數（含可視 = 4+1+4 = 9 頁）
    _MAX_CONCURRENT = 3         # 同時載入上限

    def _build_scroll(self) -> QWidget:
        """建立連續滾動閱讀容器

        核心機制 — 前綴和偏移表 (prefix-sum offset table)
        ------------------------------------------------
        _page_offsets[i] = sum of _page_heights[0..i-1] (長度 = total_pages + 1)
        - 初始時所有頁面使用估計高度 _est_page_h (=1100px) 填充，
          確保 scrollbar 範圍正確，layout 不因圖片載入而抖動。
        - 每頁對應一個 QLabel，初始尺寸為固定佔位尺寸。
        - 圖片載入完成後呼叫 _update_page_height() 校正真實高度，
          並更新後續所有 offset。

        滾動事件處理 (debounce)
        -----------------------
        - _scroll_debounce 是一個單次 (single-shot) 計時器，間隔 30ms。
        - 每次 valueChanged 觸發時重啟計時器 → 持續滾動時不會觸發載入。
        - 滾動停止 30ms 後 _do_scroll 被執行：
            1. 二分搜尋 (bisect_right) 找出第一個可視頁面
            2. 計算載入範圍 [first_vis - buffer, first_vis + buffer*2]
            3. 呼叫 _load_viewport() 啟動非同步載入
            4. 呼叫 _unload_far() 釋放遠端頁面的 QPixmap (保留 label 固定尺寸)

        :return: 包裝了 QScrollArea 的 QWidget
        """
        # ── 前綴和偏移表 ──
        # _page_offsets[i] = sum of heights 0..i-1 (長度 = total+1)
        # 載入前用估計值，載入後更新為真實值
        self._page_heights: List[int] = []      # 每頁實際/估計高度
        self._page_offsets: List[int] = [0]     # 前綴和，長度 total+1
        self._scroll_loading: set = set()       # 正在載入中的頁碼集合 (用於並發上限控制)
        self._est_page_h = 1100                 # 初始估計高度，隨實際載入移動平均更新

        content = QWidget()
        content.setStyleSheet("background: #0d0d0d;")
        col = QVBoxLayout(content)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._scroll_labels: List[QLabel] = []
        placeholder_w = 800
        for i in range(self._total_pages):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            lbl.setStyleSheet("background: transparent; padding: 0; margin: 0; border: none;")
            # 設定初始佔位尺寸，確保 layout 與 _page_offsets 永遠一致
            lbl.setFixedSize(placeholder_w, self._est_page_h)
            col.addWidget(lbl)
            self._scroll_labels.append(lbl)
            self._page_heights.append(self._est_page_h)
            self._page_offsets.append(self._page_offsets[-1] + self._est_page_h)

        self._scroll_area = scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #0d0d0d; }")
        scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { background: #0d0d0d; width: 6px; }
            QScrollBar::handle:vertical { background: #3a3a3c; border-radius: 3px; min-height: 30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        wrapper = QWidget()
        wrapper.setStyleSheet("background: #0d0d0d;")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(scroll)

        # ── scroll 事件：可視範圍 + 載入 + 卸載 ──
        # 持久 debounce timer：只建立一次，重複 start() 即可
        self._scroll_debounce = QTimer(self)
        self._scroll_debounce.setSingleShot(True)
        self._scroll_debounce.setInterval(30)

        def _do_scroll():
            """滾動 debounce 完成後執行：更新頁碼、載入可視範圍、卸載遠端"""
            if self._closing:
                return
            sb = scroll.verticalScrollBar()
            top = sb.value()

            # 二分搜尋 _page_offsets（嚴格遞增前綴和）
            # bisect_right 回傳第一個 > top 的位置，減 1 即為目前可視頁
            first_vis = max(0, bisect.bisect_right(self._page_offsets, top) - 1)
            if first_vis >= self._total_pages:
                first_vis = self._total_pages - 1

            # 更新頁碼追蹤
            if self._current_page != first_vis:
                self._current_page = first_vis
                self._update_title()

            load_first = max(0, first_vis - self._SCROLL_BUFFER)
            load_last = min(self._total_pages - 1, first_vis + self._SCROLL_BUFFER * 2 + 1)

            self._load_viewport(load_first, load_last)
            self._unload_far(first_vis, self._SCROLL_BUFFER + 2)

        self._scroll_debounce.timeout.connect(_do_scroll)

        def _on_scroll(_unused=None) -> None:
            """scrollbar valueChanged handler — 重啟 debounce timer"""
            if self._closing:
                return
            self._scroll_debounce.start()  # 重啟 timer，30ms 內再次滾動則重置

        scroll.verticalScrollBar().valueChanged.connect(_on_scroll)
        # 首次載入：視窗顯示後馬上載入前 5 頁
        QTimer.singleShot(50, lambda: self._load_viewport(0, min(5, self._total_pages)))

        return wrapper

    # ── 偏移表更新 ──────────────────────────────────

    def _update_page_height(self, idx: int, actual_h: int) -> None:
        """頁面 idx 載入完成後，更新前綴和 + 估計值

        O(n) 的後綴更新，但只在每頁首次載入時呼叫一次（非 scroll 每幀），
        因此對效能無顯著影響。

        :param idx: 頁碼 (0-based)
        :param actual_h: 圖片實際高度 (px)，由 _apply_scroll_img 回傳的縮放後高度
        """
        if actual_h <= 0:
            return
        old_h = self._page_heights[idx]
        delta = actual_h - old_h
        self._page_heights[idx] = actual_h
        # 更新前綴和：idx+1 之後全部加上差值
        for j in range(idx + 1, self._total_pages + 1):
            self._page_offsets[j] += delta
        # 移動平均估計（3:1 權重，平滑適應不同頁面尺寸變化）
        self._est_page_h = (self._est_page_h * 3 + actual_h) // 4

    # ── 載入與卸載 ──────────────────────────────────

    def _load_viewport(self, first: int, last: int) -> None:
        """載入指定範圍內尚未載入的頁面（並發上限控制）

        對於範圍中每一頁，跳過三種情況：
        1. 已在快取 — 直接套用圖片 (apply_scroll_img)
        2. 已在載入中 (_scroll_loading) — 跳過
        3. 已達並發上限 (_MAX_CONCURRENT = 3) — 跳出迴圈，
           由 _continue_loading 在 _done 回呼中補載

        注意閉包變數綁定：pg=i 將 i 的目前值（by value）綁定到預設引數，
        避免 for 迴圈結束後 i 變成最後值 (late-binding 問題)。

        :param first: 載入起始頁碼（含）
        :param last: 載入結束頁碼（含）
        """
        for i in range(first, last + 1):
            if i >= self._total_pages:
                break
            cached = self._cache.get(i)
            if cached is not None:
                scaled_h = self._apply_scroll_img(i, cached)
                if scaled_h > 0:
                    self._update_page_height(i, scaled_h)
                continue
            if i in self._scroll_loading:
                continue
            if len(self._scroll_loading) >= self._MAX_CONCURRENT:
                break

            self._scroll_loading.add(i)

            def _load(pg=i) -> Optional[bytes]:
                if pg >= len(self._image_files):
                    return None
                return _load_image_bytes(self._comic_path, self._is_compressed,
                                         self._image_files[pg])

            def _done(data: Optional[bytes], pg=i) -> None:
                self._scroll_loading.discard(pg)
                if self._closing or pg >= len(self._scroll_labels):
                    return
                pm = _bytes_to_pixmap(data)
                if pm is None:
                    QTimer.singleShot(0, self._continue_loading)
                    return

                self._cache.put(pg, pm)
                scaled_h = self._apply_scroll_img(pg, pm)
                if scaled_h > 0:
                    self._update_page_height(pg, scaled_h)

                # 載入完成後嘗試繼續載入剩餘頁面
                QTimer.singleShot(0, self._continue_loading)

            self._async(_load, _done)

    def _continue_loading(self) -> None:
        """在 _done 回呼中觸發，補載因並發上限被跳過的可視範圍頁面

        當 _load_viewport 因 _MAX_CONCURRENT 限制提前跳出迴圈時，
        未載入的頁面會由已完成的頁面之 _done 回呼呼叫此方法補載。
        形成「載入完成 → 檢查可視範圍 → 啟動下一批載入」的鏈式驅動。
        """
        if self._closing or not hasattr(self, '_scroll_area') or self._scroll_area is None:
            return
        sb = self._scroll_area.verticalScrollBar()
        top = sb.value()
        first_vis = max(0, bisect.bisect_right(self._page_offsets, top) - 1)
        if first_vis >= self._total_pages:
            first_vis = self._total_pages - 1
        load_first = max(0, first_vis - self._SCROLL_BUFFER)
        load_last = min(self._total_pages - 1, first_vis + self._SCROLL_BUFFER * 2 + 1)
        self._load_viewport(load_first, load_last)

    def _unload_far(self, center: int, buffer: int) -> None:
        """釋放遠離視口的頁面 QPixmap（保留 label 尺寸以維持 layout 穩定）

        QLabel.clear() 只清除 pixmap 內容，釋放 GPU / 系統記憶體，
        但 label 的 fixedSize 保持不變 → scrollbar 範圍不受影響。

        :param center: 目前可視頁碼 (0-based)
        :param buffer: 保留範圍半徑（兩側各 buffer 頁）
        """
        keep_min = max(0, center - buffer)
        keep_max = min(self._total_pages - 1, center + buffer * 2)
        for i in range(0, self._total_pages):
            if keep_min <= i <= keep_max:
                continue
            lbl = self._scroll_labels[i]
            if lbl.pixmap() is not None:
                lbl.clear()  # 只清除 pixmap 釋放 GPU 記憶體，不改變 label 尺寸

    def _apply_scroll_img(self, idx: int, pm: QPixmap) -> int:
        """將 QPixmap 縮放後套用到對應的 scroll label

        縮放策略：以 viewport 寬度為基礎，留 40px 邊距，上限 800px。
        若 viewport 尚未完成 layout (width < 100px) 則使用預設 800px。
        縮放後同時更新 label 的 fixedSize 以保持 layout 一致。

        :param idx: 頁碼 (0-based)
        :param pm: 原始 QPixmap
        :return: 套用後的縮放高度（px），用於更新前綴和偏移表；
                 若提前退出則回傳 0
        :rtype: int
        """
        if self._closing or self._scroll_area is None or idx >= len(self._scroll_labels):
            return 0
        if pm.width() <= 0 or pm.height() <= 0:
            return 0
        vp = self._scroll_area.viewport()
        vp_w = vp.width() if vp else self.width()
        max_w = min(vp_w - 40, 800)
        if max_w < 100:
            max_w = 800  # fallback：視窗尚未完成 layout
        scaled = pm.scaled(max_w, pm.height() * max_w // pm.width(),
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        self._scroll_labels[idx].setPixmap(scaled)
        self._scroll_labels[idx].setFixedSize(scaled.width(), scaled.height())
        return scaled.height()

    # ── 翻頁導航 ──────────────────────────────────────

    def _show_page(self, page: int) -> None:
        """跳轉到指定頁碼

        SINGLE/DOUBLE 模式：交由 _PageView.show_page 觸發非同步載入 + 重繪。
        SCROLL 模式：頁碼追蹤由 _do_scroll 在 scroll 事件中處理，
                    此處僅更新標題（不觸發 scroll 跳轉，避免打斷使用者滾動）。

        :param page: 目標頁碼 (0-based)，會被 clamp 到合法範圍
        """
        if self._total_pages == 0:
            return
        self._current_page = max(0, min(page, self._total_pages - 1))

        if self._mode == ReadingMode.SCROLL:
            self._update_title()
            return

        if isinstance(self._display_widget, _PageView):
            self._display_widget.show_page(self._current_page, self)
        self._update_title()

    def _go_prev(self) -> None:
        """上一頁（按鈕 / 鍵盤 Left/Up）"""
        if self._current_page > 0:
            self._show_page(self._current_page - 1)

    def _go_next(self) -> None:
        """下一頁（按鈕 / 鍵盤 Right/Down）"""
        if self._current_page < self._total_pages - 1:
            self._show_page(self._current_page + 1)

    def _update_title(self) -> None:
        """更新頁碼標籤、導航按鈕啟用狀態、視窗標題"""
        self._prev_btn.setEnabled(self._current_page > 0)
        self._next_btn.setEnabled(self._current_page < self._total_pages - 1)
        self._page_label.setText(f"{self._current_page+1} / {self._total_pages}")
        self.setWindowTitle(self._window_title())

    # ── 鍵盤事件 ──────────────────────────────────────

    def keyPressEvent(self, event: Optional[QKeyEvent]) -> None:
        """鍵盤快捷鍵

        - SINGLE/DOUBLE 模式：Left/Up = 上一頁，Right/Down = 下一頁，Esc = 關閉
        - SCROLL 模式：委託給 super()，讓 QScrollArea 處理 PgUp/PgDn/方向鍵
        """
        if event is None:
            return
        if self._mode == ReadingMode.SCROLL:
            super().keyPressEvent(event)
            return
        k = event.key()
        if k in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            self._go_prev()
        elif k in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            self._go_next()
        elif k == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # ── 關閉 ──────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """優雅關閉策略

        1. 設 _closing = True → 所有進行中的 _done / _on_scroll 等 callback
           檢測到該旗標後直接 return，避免存取已銷毀的 Qt 物件
        2. 清空圖片快取釋放記憶體
        3. 不碰 _workers 列表 — 這些 worker thread 結束時會自動觸發
           finished signal → _cleanup 自行從列表移除
        """
        self._closing = True
        self._cache.clear()
        # worker 列表留著 — thread 結束後 cleanup 會自行移除
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════
# 頁面顯示（單頁 / 雙頁模式共用）
# ═══════════════════════════════════════════════════════
class _PageView(QWidget):
    """自繪頁面元件 — 支援單頁 (SINGLE) 與雙頁並排 (DOUBLE)

    使用 QPainter 自訂繪圖，透過共享的 _ImageCache（來自父 ComicReaderWidget）
    取得 QPixmap 後縮放至視窗尺寸。所有縮放在 paintEvent 中即時計算，
    因此無須單獨處理 resize 邏輯 — resizeEvent 僅觸發 update() 重繪。

    非同步載入由 show_page() 發起，callback 完成後呼叫 self.update() 觸發重繪。
    """

    def __init__(self, reader: ComicReaderWidget, mode: ReadingMode) -> None:
        """
        :param reader: 父閱讀器實例，用於存取 cache、comic_path 等狀態
        :param mode: ReadingMode.SINGLE 或 ReadingMode.DOUBLE
        """
        super().__init__(reader)
        self._reader = reader
        self._mode = mode
        self._page = 0

        self.setStyleSheet("background: #0d0d0d;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(200, 150)

    def show_page(self, page: int, reader: ComicReaderWidget) -> None:
        """設定目前頁碼並觸發非同步載入

        呼叫流程：
        1. 更新 self._page
        2. DOUBLE 模式：載入 page 與 page+1 兩頁；SINGLE：只載入 page
        3. 快取命中 → 直接 self.update() 觸發重繪
        4. 快取未命中 → 啟動非同步載入 (reader._async)，完成後 self.update()

        閉包變數 p=pg 透過預設引數 by-value 綁定，避免 late-binding。

        :param page: 目標頁碼 (0-based)
        :param reader: 父 ComicReaderWidget（與 self._reader 相同，但保持參數一致性）
        """
        self._page = page

        if reader._closing:
            return

        # 需要載入的頁碼
        pages = [page]
        if self._mode == ReadingMode.DOUBLE and page + 1 < reader._total_pages:
            pages.append(page + 1)

        for pg in pages:
            if reader._cache.get(pg) is not None:
                self.update()
                continue
            if pg >= len(reader._image_files):
                continue

            def _load(p=pg) -> Optional[bytes]:
                if p >= len(reader._image_files):
                    return None
                return _load_image_bytes(reader._comic_path, reader._is_compressed,
                                         reader._image_files[p])

            def _done(data: Optional[bytes], p=pg) -> None:
                if reader._closing:
                    return
                pm = _bytes_to_pixmap(data)
                if pm:
                    reader._cache.put(p, pm)
                self.update()

            reader._async(_load, _done)

    def paintEvent(self, event) -> None:
        """Qt paint event — 使用 QPainter 繪製圖片

        若 _closing 旗標已設定則直接 return，避免存取已銷毀的資源。
        """
        if self._reader._closing:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self._mode == ReadingMode.DOUBLE:
            self._paint_double(painter)
        else:
            self._paint_single(painter)

        painter.end()

    def _paint_single(self, painter: QPainter) -> None:
        """繪製單頁（fit-to-window）

        縮放演算法：
        1. 先以視窗寬度為基準，減去 4px 邊距
        2. 按圖片長寬比計算高度
        3. 若高度超出視窗高度，改以高度為基準重新計算寬度
        4. 置中繪製

        若圖片尚未載入，顯示「載入中…」佔位文字。
        """
        pm = self._reader._cache.get(self._page)
        if pm is None or pm.isNull():
            painter.setPen(QColor("#8e8e93"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "載入中…")
            return

        w, h = self.width(), self.height()
        r = pm.width() / pm.height() if pm.height() > 0 and pm.width() > 0 else 1
        dw = w - 4
        dh = int(dw / r)
        if dh > h - 4:
            dh = h - 4
            dw = int(dh * r)
        painter.drawPixmap((w - dw) // 2, (h - dh) // 2, dw, dh, pm)

    def _paint_double(self, painter: QPainter) -> None:
        """繪製雙頁並排（左右各一頁，8px 間距）

        佈局：
        ┌───────┐ ─ ─ ─ ┌───────┐
        │ 左頁   │  8px  │ 右頁   │
        │ (N)    │ gap   │ (N+1)  │
        └───────┘ ─ ─ ─ └───────┘

        每頁的縮放演算法與 _paint_single 相同（fit-to-half-width）。
        右頁若為 None（例如最後一頁為奇數時），直接跳過不繪製。
        """
        cache = self._reader._cache
        p0 = cache.get(self._page)
        p1 = cache.get(self._page + 1)

        if p0 is None or p0.isNull():
            painter.setPen(QColor("#8e8e93"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "載入中…")
            return

        w, h = self.width(), self.height()
        gap = 8
        half = (w - gap) // 2

        for idx, pm in [(0, p0), (1, p1)]:
            if pm is None or pm.isNull():
                continue
            r = pm.width() / pm.height() if pm.height() > 0 and pm.width() > 0 else 1
            dw = half - 4
            dh = int(dw / r)
            if dh > h - 4:
                dh = h - 4
                dw = int(dh * r)
            x = idx * (half + gap) + (half - dw) // 2
            y = (h - dh) // 2
            painter.drawPixmap(x, y, dw, dh, pm)

    def resizeEvent(self, event) -> None:
        """視窗大小改變時觸發重繪，paintEvent 內會重新計算縮放比例"""
        super().resizeEvent(event)
        self.update()
