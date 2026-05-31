#####
# 通用且常用的函式
#####
import re


NAMESPACE_KEY_PATTERN = re.compile(r"^(?:(?P<namespace>[^:]+):)?(?P<key>.+)$")

def parseNamespacedKey(info_key: str, default_namespace: str = "base") -> tuple[str, str]:
    """解析namespace:key的結構

    Args:
        info_key (str): 字串
        default_namespace (str, optional): 預設namespace. Defaults to "base".

    Raises:
        ValueError: 發生比對錯誤

    Returns:
        tuple[str, str]: (namespace, key)
    """
    match = NAMESPACE_KEY_PATTERN.match(info_key)
    if not match:
        raise ValueError(f"Invalid info_key: {info_key}")
    
    namespace = match.group("namespace") or default_namespace
    key = match.group("key")
    return namespace, key
