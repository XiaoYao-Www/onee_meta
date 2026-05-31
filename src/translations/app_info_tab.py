"""翻譯: 關於分頁 (app_info_tab)"""
from types import MappingProxyType
from src.classes.view.lazy_str import LazyStr

APP_INFO_TAB = MappingProxyType({
    "👻 作者資訊": LazyStr("👻 作者資訊", "app_info_tab"),
    "自我介紹": LazyStr(
        "逍遙 ( Xiao Yao )\n"
        "觀繁花而不與其爭艷\n"
        "處江湖而不染其煙塵", "app_info_tab"
    ),
    "作者 Github 連結": LazyStr("作者 Github 連結", "app_info_tab"),
    "📦 軟體資訊": LazyStr("📦 軟體資訊", "app_info_tab"),
    "軟體介紹": LazyStr(
        "版本: {version}\n"
        "姐姐大人永遠是對的", "app_info_tab"
    ),
    "專案 GitHub 專案連結": LazyStr("專案 GitHub 專案連結", "app_info_tab"),
})
