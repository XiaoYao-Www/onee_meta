"""翻譯聚合器 — 向後相容 TR.MAIN_VIEW / TR.COMIC_LIST_VIEW 等存取"""

from src.translations import main_view
from src.translations import comic_list_view
from src.translations import main_controller
from src.translations import operation_area
from src.translations import app_info_tab
from src.translations import app_setting_tab
from src.translations import info_editor_tab
from src.translations import ui_widgets


class _TR:
    """翻譯命名空間聚合器"""

    MAIN_VIEW = main_view.MAIN_VIEW
    COMIC_LIST_VIEW = comic_list_view.COMIC_LIST_VIEW
    MAIN_CONTROLLER = main_controller.MAIN_CONTROLLER
    OPERATION_AREA = operation_area.OPERATION_AREA
    APP_INFO_TAB = app_info_tab.APP_INFO_TAB
    APP_SETTING_TAB = app_setting_tab.APP_SETTING_TAB
    INFO_EDITOR_TAB = info_editor_tab.INFO_EDITOR_TAB
    UI_WIDGETS = ui_widgets.UI_WIDGETS


TR = _TR()
