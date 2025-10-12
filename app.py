import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator
from PySide6.QtGui import QIcon
# 自訂庫
import src.app_config as APP_CONFIG
from src.model.main_model import MainModel
from src.view.main_view import MainView
from src.controller.main_controller import MainController

if __name__ == "__main__":
    # 1. 應用初始化
    application = QApplication(sys.argv)
    application.setWindowIcon(QIcon(APP_CONFIG.appIconPath))

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