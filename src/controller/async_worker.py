"""
通用非同步執行引擎 — 將耗時操作移至 QThread，避免 UI 凍結

用法:
    from src.controller.async_worker import run_async

    def long_work():
        time.sleep(5)
        return "done"

    def on_result(data):
        print(f"Got: {data}")

    run_async(long_work, on_result=on_result)
"""
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot


class WorkerSignals(QObject):
    """Worker 對外溝通的信號組"""
    started = Signal()
    progress = Signal(str, int, int)  # (message, current, max)
    result = Signal(object)          # 回傳值
    error = Signal(str)              # 錯誤訊息
    finished = Signal()


class AsyncWorker(QObject):
    """在 QThread 中執行一個可呼叫物件"""

    def __init__(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        """QThread 啟動後自動呼叫"""
        try:
            self.signals.started.emit()
            result = self._fn(*self._args, **self._kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


def run_async(
    fn: Callable,
    *,
    on_result: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[str, int, int], None]] = None,
    on_finished: Optional[Callable[[], None]] = None,
) -> tuple[QThread, AsyncWorker]:
    """建立並啟動一個非同步任務

    Args:
        fn: 要在背景執行緒中執行的函式
        on_result: 成功時回調 (主執行緒)
        on_error: 失敗時回調，引數為錯誤訊息字串
        on_progress: 進度回調 (message, current, max)
        on_finished: 無論成功/失敗，執行緒結束後回調

    Returns:
        (QThread, AsyncWorker) — 保存引用避免被 GC
    """
    thread = QThread()
    worker = AsyncWorker(fn)
    worker.moveToThread(thread)

    # 生命週期串接
    thread.started.connect(worker.run)
    worker.signals.finished.connect(thread.quit)
    worker.signals.finished.connect(worker.deleteLater)  # type: ignore[attr-defined]
    thread.finished.connect(thread.deleteLater)          # type: ignore[attr-defined]

    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_progress:
        worker.signals.progress.connect(on_progress)
    if on_finished:
        worker.signals.finished.connect(on_finished)

    thread.start()
    return thread, worker
