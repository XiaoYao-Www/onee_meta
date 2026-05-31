"""翻譯: 漫畫列表 (comic_list_view)"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

COMIC_LIST_VIEW = MappingProxyType({
    "選擇漫畫資料夾路徑": LazyStr("選擇漫畫資料夾路徑", "comic_list_view"),
    "手動": LazyStr("手動", "comic_list_view"),
    "檔名": LazyStr("檔名", "comic_list_view"),
    "集數": LazyStr("集數", "comic_list_view"),
    "{selected} / {total} 本漫畫": LazyStr("{selected} / {total} 本漫畫", "comic_list_view"),
    "選擇漫畫資料夾": LazyStr("選擇漫畫資料夾", "comic_list_view"),
})
