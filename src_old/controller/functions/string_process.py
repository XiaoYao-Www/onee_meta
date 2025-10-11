

def resolve_placeholders(s: str, placeholders: dict[str, str]) -> str:
    """替換字串中的佔位符

    Args:
        s (str): 原始字串
        placeholders (dict[str, str]): 佔位符對應的值

    Returns:
        str: 替換後的字串
    """
    for key, value in placeholders.items():
        s = s.replace(f"{{{key}}}", value)
    return s