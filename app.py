#####
# 應用主入口
#####
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, Qt
from PySide6.QtGui import QIcon
# 自訂庫
from src.logging_config import setup_logging, get_logger
import src.app_config as APP_CONFIG
from src.model.main_model import MainModel
from src.view.main_view import MainView
from src.controller.main_controller import MainController

_log = get_logger(__name__)

if __name__ == "__main__":
    setup_logging()

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # 1. 應用初始化
    application = QApplication(sys.argv)
    application.setWindowIcon(QIcon(APP_CONFIG.appIconPath))

    # 載入全域樣式表
    qss_path = Path("assets/style.qss")
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            application.setStyleSheet(f.read())
        _log.info("載入樣式表: %s", qss_path)

    # 2. 資源初始化
    model = MainModel()
    translator = QTranslator()

    # 3. MVC 組裝
    view = MainView()
    controller = MainController(
        model=model,
        view=view,
        application=application,
        translator=translator
    )

    # 4. 啟動
    view.show()
    sys.exit(application.exec())