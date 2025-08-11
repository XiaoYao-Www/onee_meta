from PySide6.QtCore import QObject, QTranslator
from PySide6.QtWidgets import QApplication
# 自訂庫
from src.model.main_model import MainModel
from src.view.main_view import MainView

class MainController(QObject):
    """主控制
    """
    def __init__(self, model:MainModel, view: MainView, application: QApplication, translator: QTranslator) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.application = application
        self.translator = translator