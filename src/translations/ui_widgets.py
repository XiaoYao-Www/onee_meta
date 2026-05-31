"""翻譯: 通用 widgets"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

UI_WIDGETS = MappingProxyType({
    "輸入{keep}保留原值": LazyStr("輸入{keep}保留原值", "ui_widgets"),
})
