#####
# 主控制器 — 非同步版本
#####
from PySide6.QtCore import QObject, QTranslator, QModelIndex, QItemSelectionModel
from PySide6.QtWidgets import QApplication
from typing import List, Optional, cast
# 自訂庫
from src.classes.calibre_scanner import CalibreSidecar
from src.classes.model.comic_data import XmlComicInfo, ComicData
from src.model.main_model import MainModel
from src.model.functions.comic_read_write import readComicFolder
from src.view.main_view import MainView
from src.signal_bus import SIGNAL_BUS
from src.translations import TR
from src.controller.batch_processor import BatchProcessor
from src.controller.async_worker import run_async
from src.logging_config import get_logger

_log = get_logger(__name__)


class MainController(QObject):
    """主控制
    """
    def __init__(self, model: MainModel, view: MainView, application: QApplication, translator: QTranslator) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.application = application
        self.translator = translator

        # 保存異步 worker 引用，防 GC
        self._async_workers: list = []

        self.application_linkage_structure()
        self.signal_connection()
        self.application_init()

    ### 初始化 ###

    def application_linkage_structure(self) -> None:
        self.view.left_widget.setListModel(self.model.comicListModel)

    def application_init(self) -> None:
        # 語言選項
        tab = self.view.right_widget.app_setting_tab
        tab.lang_select_combo.clear()
        items: list[str] = list(self.model.runningStore.get("translation_files", {}).keys())
        items.insert(0, "")
        tab.lang_select_combo.addItems(items)

        self.setAppFontSize(self.model.appSetting.get("font_size", 10))
        self.setImageExt(self.model.appSetting.get("image_exts", []))
        self.setAllowFile(self.model.appSetting.get("allow_files", []))
        self.changeLang(self.model.appSetting.get("lang", ""))
        self.setCalibrePath(self.model.appSetting.get("calibre_path", ""))

    ### 信號連接 ###

    def signal_connection(self) -> None:
        bus = SIGNAL_BUS
        bus.uiSend.selectComicFolder.connect(self.selectComicFolder)
        bus.uiSend.comicListSelected.connect(self.selectComic)
        bus.uiSend.startProcess.connect(self.startProcess)
        bus.uiSend.runScanner.connect(self.runScanner)
        bus.uiSend.fontSizeSet.connect(self.setAppFontSize)
        bus.uiSend.imgExtensionSet.connect(self.setImageExt)
        bus.uiSend.allowFileSet.connect(self.setAllowFile)
        bus.uiSend.langChange.connect(self.changeLang)
        bus.uiSend.carlibrePathSet.connect(self.setCalibrePath)
        self.model.comicListModel.listIndexChanged.connect(self.comicListIndexChanged)
        bus.uiSend.comicListSort.connect(lambda x: self.model.comicListSorted(x))

    # ── 輔助：追蹤 async worker ─────────────────────────

    def _track(self, thread, worker) -> None:
        """保存 async worker 引用，完成後自動清理"""
        self._async_workers.append((thread, worker))
        worker.signals.finished.connect(lambda: self._async_workers.clear())

    # ── 應用功能 ────────────────────────────────────────

    def runScanner(self, name: str, author: str, isbn: str) -> None:
        """非同步：在背景執行 Calibre 元數據搜尋"""
        calibre_path = self.model.appSetting.get("calibre_path", "")
        self.view.loading.show()
        self.view.loading.setInfoText("正在搜尋元數據...")
        _log.info("開始搜尋 Calibre 元數據")

        def _work() -> Optional[list]:
            scanner = CalibreSidecar(calibre_path)
            return scanner.fetch_metadata(
                title=name or None,
                authors=author or None,
                isbn=isbn or None,
            )

        def _on_result(data: Optional[list]) -> None:
            if data:
                self.view.right_widget.info_editor_tab.update_data_cards(data)
                self.view.setStatus(f"搜尋完成，取得 {len(data)} 筆結果")
            else:
                self.view.setStatus("搜尋無結果")
            self.view.loading.close()

        def _on_error(msg: str) -> None:
            self.view.loading.close()
            SIGNAL_BUS.uiRevice.sendCritical.emit("搜尋錯誤", msg)

        t, w = run_async(_work, on_result=_on_result, on_error=_on_error)
        self._track(t, w)

    def selectComic(self, comic: list[int]) -> None:
        """漫畫選擇"""
        area = self.view.right_widget
        if len(comic) < 1:
            area.tabs.setTabVisible(area.index_info_editor_tab, False)
            return

        if not area.tabs.isTabVisible(area.index_info_editor_tab):
            area.tabs.setTabVisible(area.index_info_editor_tab, True)
            area.tabs.setCurrentIndex(area.index_info_editor_tab)

        uuid_list: list[str] = self.model.runningStore.get("comic_uuid_list", [])
        selected: list[str] = [uuid_list[i] for i in comic]
        self.model.runningStore.set("selected_comics", selected)

        comic_data_list: list[ComicData] = [
            data for u in selected
            if (data := self.model.comicDataStore.get(u)) is not None
        ]
        self.view.right_widget.info_editor_tab.setComicInfoData(comic_data_list)

    def selectComicFolder(self, folder: str) -> None:
        """非同步：在背景掃描漫畫資料夾"""
        # 在主執行緒擷取設定 (避免 QObject 跨執行緒存取)
        img_exts = self.model.appSetting.get("image_exts", [])
        allow_files = self.model.appSetting.get("allow_files", [])

        # UI 即時更新
        self.view.loading.show()
        self.view.loading.setInfoText("正在掃描漫畫資料夾...")
        self.view.left_widget.comic_path_button.setText(folder)
        self.view.left_widget.comic_path_button.setToolTip(folder)
        self.view.right_widget.tabs.setTabVisible(
            self.view.right_widget.index_info_editor_tab, False
        )
        _log.info("開始非同步載入漫畫: %s", folder)

        def _work() -> dict:
            """Worker thread: 純 I/O"""
            return readComicFolder(folder, img_exts, allow_files)

        def _on_result(comic_data: dict) -> None:
            """Main thread: 更新 Model + View"""
            self.model.runningStore.set("comic_folder_path", folder)
            self.model.runningStore.set("selected_comics", [])
            self.model.comicDataStore.clear()
            self.model.comicDataStore.update(comic_data)

            self.model.comicListModel.beginResetModel()
            uuid_list = list(comic_data.keys())
            self.model.runningStore.set("comic_uuid_list", uuid_list)
            self.model.comicListModel.uuidList = uuid_list
            self.model.comicListModel.endResetModel()

            self.view.left_widget.changeInfoLabel(
                select=0, total=len(comic_data)
            )
            self.view.setStatus(f"已載入 {len(comic_data)} 本漫畫")
            self.view.loading.close()
            _log.info("漫畫載入完成: %d 本", len(comic_data))

        def _on_error(msg: str) -> None:
            self.view.loading.close()
            SIGNAL_BUS.uiRevice.sendCritical.emit("載入錯誤", msg)

        t, w = run_async(_work, on_result=_on_result, on_error=_on_error)
        self._track(t, w)

    def startProcess(self) -> None:
        """非同步：在背景批次寫入漫畫資料"""
        editor_data: XmlComicInfo = self.view.right_widget.info_editor_tab.getComicInfoData()
        uuid_select: list[str] = self.model.runningStore.get("selected_comics", [])
        comic_all_list: list[str] = self.model.runningStore.get("comic_uuid_list", [])

        if not uuid_select or not comic_all_list:
            return

        self.view.loading.show()
        self.view.loading.setProgress(0, len(uuid_select), "準備批次處理...")
        _log.info("開始批次處理 %d 本漫畫", len(uuid_select))

        def _work(on_progress=None) -> dict:
            """Worker thread: 逐一寫入漫畫"""
            from copy import deepcopy
            from datetime import datetime
            import os
            from src.controller.functions.placeholder_process import XmlDataPlaceholderProcess
            from src.controller.functions.xml_data_process import updataXmlComicInfo
            from src.classes.controller.comic_placeholder_data import ComicPlaceholderData

            fail_count = 0
            for order, uuid in enumerate(uuid_select, start=1):
                comic_data = self.model.comicDataStore.get(uuid)
                if comic_data is None:
                    fail_count += 1
                    continue

                # 建立佔位符
                fname = os.path.basename(comic_data["comic_path"])
                file_name, file_ext = os.path.splitext(fname)
                parent_folder = os.path.basename(os.path.dirname(comic_data["comic_path"]))
                now = datetime.now()
                raw_title = str(
                    comic_data.get("xml_comic_info", {})
                    .get("fields", {}).get("base", {}).get("Title", "")
                ).replace(" 🔒", "").replace("🔒", "")

                placeholder = ComicPlaceholderData(
                    index=comic_all_list.index(uuid) + 1,
                    order=order,
                    file_name=file_name,
                    file_ext=file_ext,
                    parent_folder=parent_folder,
                    year=str(now.year),
                    month=f"{now.month:02d}",
                    day=f"{now.day:02d}",
                    date=now.strftime("%Y-%m-%d"),
                    clear_old_title=raw_title,
                    image_count=comic_data.get("image_count", 0),
                )

                processed = XmlDataPlaceholderProcess(editor_data, placeholder)
                old_xml = comic_data.get("xml_comic_info")
                if old_xml is None:
                    fail_count += 1
                    continue

                backup = deepcopy(old_xml)
                updataXmlComicInfo(old_xml, processed)

                if not self.model.writeComic(uuid):
                    comic_data["xml_comic_info"] = backup
                    fail_count += 1

                if on_progress:
                    on_progress(order, len(uuid_select))

            return {
                "success": len(uuid_select) - fail_count,
                "fail": fail_count,
                "total": len(uuid_select),
            }

        def _on_progress(current: int, total: int) -> None:
            """透過 WorkerSignals.progress 回呼到主執行緒"""
            self.view.loading.setProgress(current, total, f"處理中 {current}/{total}")

        def _on_result(stats: dict) -> None:
            self.model.comicListModel.layoutChanged.emit()
            self.view.left_widget.setSortType(0)
            self.view.loading.close()

            if stats["fail"] > 0:
                self.view.setStatus(f"處理完成，{stats['fail']} 筆失敗")
                SIGNAL_BUS.uiRevice.sendCritical.emit(
                    "處理完成", f"已完成處理，但有 {stats['fail']} 筆寫入失敗。"
                )
            else:
                self.view.setStatus(f"成功處理 {stats['success']} 本漫畫")
                SIGNAL_BUS.uiRevice.sendInformation.emit(
                    "處理完成", f"成功處理 {stats['success']} 本漫畫。"
                )

        def _on_error(msg: str) -> None:
            self.view.loading.close()
            SIGNAL_BUS.uiRevice.sendCritical.emit("處理錯誤", msg)

        t, w = run_async(_work, on_result=_on_result, on_error=_on_error)
        # progress 信號需要從 worker thread 發送到主執行緒
        w.signals.progress.connect(lambda msg, cur, m: _on_progress(cur, m))
        self._track(t, w)

    # ── 連接功能 ────────────────────────────────────────

    def comicListIndexChanged(self, uuidList: list[str]) -> None:
        select_model = self.view.left_widget.comic_list.selectionModel()
        select_model.clearSelection()

        for uuid in uuidList:
            try:
                row = self.model.comicListModel.uuidList.index(uuid)
            except ValueError:
                continue
            idx = self.model.comicListModel.index(row)
            select_model.select(idx, QItemSelectionModel.SelectionFlag.Select)

        self.view.left_widget.setSortType(0)

    # ── 應用設定 ────────────────────────────────────────

    def setAllowFile(self, fileList: List[str]) -> None:
        self.model.appSetting.set("allow_files", fileList)
        self.view.right_widget.app_setting_tab.allowFilesChangedDisplay(fileList)

    def setImageExt(self, extList: List[str]) -> None:
        self.model.appSetting.set("image_exts", extList)
        self.view.right_widget.app_setting_tab.imageExtensionChangedDisplay(extList)

    def setAppFontSize(self, size: int) -> None:
        self.model.appSetting.set("font_size", size)
        self.view.changeFontSize(size)
        self.view.right_widget.app_setting_tab.fontSizeChangedDisplay(size)

    def setCalibrePath(self, path: str) -> None:
        self.model.appSetting.set("calibre_path", path)
        self.view.right_widget.app_setting_tab.calibrePathChangedDisplay(path)

    def changeLang(self, langName: str) -> None:
        lang_file = self.model.runningStore.get("translation_files", {}).get(langName)
        if lang_file is None:
            self.model.appSetting.set("lang", "")
            self.application.removeTranslator(self.translator)
            SIGNAL_BUS.uiRevice.translateUi.emit()
            if langName != "":
                SIGNAL_BUS.uiRevice.sendCritical.emit(
                    TR.MAIN_CONTROLLER["設定錯誤"](),
                    TR.MAIN_CONTROLLER["沒有目標語言檔案"](),
                )
            self.view.right_widget.app_setting_tab.langSelectedChangedDisplay("")
            return

        self.model.appSetting.set("lang", langName)
        self.translator.load(lang_file)
        self.application.installTranslator(self.translator)
        SIGNAL_BUS.uiRevice.translateUi.emit()
        self.view.right_widget.app_setting_tab.langSelectedChangedDisplay(langName)
