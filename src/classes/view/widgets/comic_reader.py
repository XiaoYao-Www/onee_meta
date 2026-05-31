"""
內建漫畫閱讀器 — 支援單頁 / 雙頁 / 滾動三種閱讀模式

用法:
    from src.classes.view.widgets.comic_reader import ComicReaderWidget

    reader = ComicReaderWidget(comic_full_path)
    reader.exec()

設計要點:
    - 追蹤 AsyncWorker 引用防止 GC 回收 thread
    - Worker 完成後個別從追蹤列表移除
    - closeEvent 只設 _closing 旗標，不 touch worker
    - 所有 async callback 入口檢查 _closing
    - QPixmap 只在主執行緒建立
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
    """LRU 圖片快取"""

    def __init__(self, max_size: int = 20) -> None:
        self._max = max_size
        self._data: Dict[int, QPixmap] = {}

    def get(self, page: int) -> Optional[QPixmap]:
        return self._data.get(page)

    def put(self, page: int, pixmap: QPixmap) -> None:
        self._data[page] = pixmap
        if len(self._data) > self._max:
            oldest = min(self._data.keys())
            del self._data[oldest]

    def evict_outside(self, keep: set) -> None:
        for k in list(self._data.keys()):
            if k not in keep:
                del self._data[k]

    def clear(self) -> None:
        self._data.clear()


# ── 非同步圖片載入 ────────────────────────────────────
def _load_image_bytes(comic_path: str, is_compressed: bool,
                      filename: str) -> Optional[bytes]:
    """在 worker thread 中讀取單張圖片，回傳 bytes"""
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
    """bytes → QPixmap（主執行緒專用）"""
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
    """內建漫畫閱讀器 — 三種閱讀模式"""

    WIDTH = 1000
    HEIGHT = 720

    def __init__(self, comic_full_path: str, parent=None) -> None:
        super().__init__(parent)
        self._comic_path = comic_full_path
        self._is_compressed = comic_full_path.lower().endswith(compressionComicExt)

        # ── 狀態 ──
        self._image_files: List[str] = []
        self._current_page: int = 0
        self._total_pages: int = 0
        self._mode: ReadingMode = ReadingMode.SINGLE
        self._closing: bool = False
        self._cache = _ImageCache(max_size=30)
        self._workers: List[Tuple] = []   # ← 必須追蹤，否則 GC 回收 QThread

        self._load_file_list()

        # ── 視窗 ──
        self.setWindowTitle(self._window_title())
        self.resize(self.WIDTH, self.HEIGHT)
        self.setMinimumSize(500, 360)
        self.setStyleSheet("background: #0d0d0d;")

        # ── 佈局 ──
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._build_toolbar(self._main_layout)

        # 顯示元件（根據模式切換）
        self._display_widget: Optional[QWidget] = None
        self._switch_mode(ReadingMode.SINGLE, self._main_layout)

        QTimer.singleShot(50, lambda: self._show_page(0))

    # ── 檔案掃描 ──────────────────────────────────────

    def _load_file_list(self) -> None:
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
        """啟動非同步載入並追蹤 thread 引用防止 GC"""
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
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setObjectName("readerToolbar")
        toolbar.setStyleSheet("""
            #readerToolbar {
                background: #1c1c1e;
                border-bottom: 1px solid rgba(255,255,255,0.08);
            }
        """)
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
        self._prev_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #e5e5e5; border: none;
                          border-radius: 5px; font-size: 12px; padding: 0 10px; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
            QPushButton:disabled { color: #555; }
        """)
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
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #8e8e93;
                border: none; border-radius: 4px; font-size: 15px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #e5e5e5; }
        """)
        close_btn.clicked.connect(self.close)

        row.addWidget(self._page_label)
        row.addSpacing(8)
        row.addWidget(close_btn)

        parent_layout.addWidget(toolbar)

    @staticmethod
    def _mode_btn_css(active: bool) -> str:
        if active:
            return ("QPushButton { background: #636366; color: #fff;"
                    " border: none; border-radius: 5px;"
                    " font-size: 12px; font-weight: 500; }")
        return ("QPushButton { background: transparent; color: #8e8e93;"
                " border: none; border-radius: 5px;"
                " font-size: 12px; font-weight: 400; }"
                "QPushButton:hover { background: rgba(255,255,255,0.08);"
                " color: #e5e5e5; }")

    def _refresh_mode_style(self) -> None:
        for m, btn in self._mode_btns.items():
            btn.setStyleSheet(self._mode_btn_css(m == self._mode))

    def _window_title(self) -> str:
        base = os.path.basename(self._comic_path)
        if self._total_pages == 0:
            return f"Reader — {base}"
        return f"Reader — {base}  ({self._current_page+1}/{self._total_pages})"

    def _on_mode_click(self, mode: ReadingMode) -> None:
        if mode == self._mode:
            return
        self._switch_mode(mode, self._main_layout)
        self._show_page(self._current_page)

    # ── 模式切換 ──────────────────────────────────────

    def _switch_mode(self, mode: ReadingMode,
                     layout: Optional[QVBoxLayout] = None) -> None:
        layout = layout or self._main_layout
        if layout is None:
            return

        self._mode = mode
        self._refresh_mode_style()

        # 移除舊顯示元件
        if self._display_widget is not None:
            layout.removeWidget(self._display_widget)
            self._display_widget.deleteLater()
            self._display_widget = None

        # 建立新顯示元件
        if mode == ReadingMode.SCROLL:
            self._display_widget = self._build_scroll()
        else:
            self._display_widget = _PageView(self, mode)

        layout.addWidget(self._display_widget, stretch=1)

        # 滾動模式隱藏翻頁按鈕
        is_scroll = (mode == ReadingMode.SCROLL)
        self._prev_btn.setVisible(not is_scroll)
        self._next_btn.setVisible(not is_scroll)

    # ── 滾動模式 ──────────────────────────────────────

    _SCROLL_BUFFER = 4          # 可視區域上下各預載頁數（含可視 = 4+1+4 = 9 頁）
    _MAX_CONCURRENT = 3         # 同時載入上限

    def _build_scroll(self) -> QWidget:
        """建立滾動閱讀容器"""
        # ── 前綴和偏移表 ──
        # _page_offsets[i] = sum of heights 0..i-1 (長度 = total+1)
        # 載入前用估計值，載入後更新為真實值
        self._page_heights: List[int] = []      # 每頁實際/估計高度
        self._page_offsets: List[int] = [0]     # 前綴和，長度 total+1
        self._scroll_loading: set = set()
        self._est_page_h = 1100

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
            if self._closing:
                return
            sb = scroll.verticalScrollBar()
            top = sb.value()

            # 二分搜尋 _page_offsets（嚴格遞增前綴和）
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
            if self._closing:
                return
            self._scroll_debounce.start()  # 重啟 timer，30ms 內再次滾動則重置

        scroll.verticalScrollBar().valueChanged.connect(_on_scroll)
        QTimer.singleShot(50, lambda: self._load_viewport(0, min(5, self._total_pages)))

        return wrapper

    # ── 偏移表更新 ──────────────────────────────────

    def _update_page_height(self, idx: int, actual_h: int) -> None:
        """頁面 idx 載入完成後，更新前綴和 + 估計值"""
        old_h = self._page_heights[idx]
        delta = actual_h - old_h
        self._page_heights[idx] = actual_h
        # 更新前綴和：idx+1 之後全部加上差值
        for j in range(idx + 1, self._total_pages + 1):
            self._page_offsets[j] += delta
        # 移動平均估計
        self._est_page_h = (self._est_page_h * 3 + actual_h) // 4

    # ── 載入與卸載 ──────────────────────────────────

    def _load_viewport(self, first: int, last: int) -> None:
        """載入指定範圍內尚未載入的頁面（並發上限控制）

        使用全域並行計數（len(_scroll_loading)），不區分範圍內外。
        _done 完成後會自動觸發 _continue_loading 繼續補載剩餘頁面。
        """
        for i in range(first, last + 1):
            if i >= self._total_pages:
                break
            if self._cache.get(i) is not None:
                self._apply_scroll_img(i, self._cache.get(i))
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
                self._apply_scroll_img(pg, pm)
                self._update_page_height(pg, pm.height())

                # 載入完成後嘗試繼續載入剩餘頁面
                QTimer.singleShot(0, self._continue_loading)

            self._async(_load, _done)

    def _continue_loading(self) -> None:
        """當 _done 觸發時檢查是否還有可視範圍內的頁面待載入"""
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
        """釋放遠離視口的頁面 QPixmap（保留 label 尺寸以維持 layout 穩定）"""
        keep_min = max(0, center - buffer)
        keep_max = min(self._total_pages - 1, center + buffer * 2)
        for i in range(0, self._total_pages):
            if keep_min <= i <= keep_max:
                continue
            lbl = self._scroll_labels[i]
            if lbl.pixmap() is not None:
                lbl.clear()  # 只清除 pixmap 釋放 GPU 記憶體，不改變 label 尺寸

    def _apply_scroll_img(self, idx: int, pm: QPixmap) -> None:
        if self._closing or idx >= len(self._scroll_labels):
            return
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

    # ── 翻頁導航 ──────────────────────────────────────

    def _show_page(self, page: int) -> None:
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
        if self._current_page > 0:
            self._show_page(self._current_page - 1)

    def _go_next(self) -> None:
        if self._current_page < self._total_pages - 1:
            self._show_page(self._current_page + 1)

    def _update_title(self) -> None:
        self._prev_btn.setEnabled(self._current_page > 0)
        self._next_btn.setEnabled(self._current_page < self._total_pages - 1)
        self._page_label.setText(f"{self._current_page+1} / {self._total_pages}")
        self.setWindowTitle(self._window_title())

    # ── 鍵盤事件 ──────────────────────────────────────

    def keyPressEvent(self, event: Optional[QKeyEvent]) -> None:
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
        """只設旗標 + 清快取，不碰 worker thread"""
        self._closing = True
        self._cache.clear()
        # worker 列表留著 — thread 結束後 cleanup 會自行移除
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════
# 頁面顯示（單頁 / 雙頁模式共用）
# ═══════════════════════════════════════════════════════
class _PageView(QWidget):
    """自繪頁面 — 單頁或雙頁並排"""

    def __init__(self, reader: ComicReaderWidget, mode: ReadingMode) -> None:
        super().__init__(reader)
        self._reader = reader
        self._mode = mode
        self._page = 0

        self.setStyleSheet("background: #0d0d0d;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(200, 150)

    def show_page(self, page: int, reader: ComicReaderWidget) -> None:
        """設定目前頁碼並觸發非同步載入"""
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
        pm = self._reader._cache.get(self._page)
        if pm is None or pm.isNull():
            painter.setPen(QColor("#8e8e93"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "載入中…")
            return

        w, h = self.width(), self.height()
        r = pm.width() / pm.height() if pm.height() > 0 else 1
        dw = w - 4
        dh = int(dw / r)
        if dh > h - 4:
            dh = h - 4
            dw = int(dh * r)
        painter.drawPixmap((w - dw) // 2, (h - dh) // 2, dw, dh, pm)

    def _paint_double(self, painter: QPainter) -> None:
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
            r = pm.width() / pm.height() if pm.height() > 0 else 1
            dw = half - 4
            dh = int(dw / r)
            if dh > h - 4:
                dh = h - 4
                dw = int(dh * r)
            x = idx * (half + gap) + (half - dw) // 2
            y = (h - dh) // 2
            painter.drawPixmap(x, y, dw, dh, pm)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update()
