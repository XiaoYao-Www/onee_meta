"""翻譯: 操作區 (operation_area)"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

OPERATION_AREA = MappingProxyType({
    "儲存編輯": LazyStr("儲存編輯", "operation_area"),
    "關於": LazyStr("關於", "operation_area"),
    "設定": LazyStr("設定", "operation_area"),
    "資訊": LazyStr("資訊", "operation_area"),
})
