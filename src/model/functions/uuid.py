#####
# UUID 庫
#####
import uuid

def newUUID4(uuidSet: set[str] = set()) -> str:
    """生成未使用過的UUID4

    Args:
        uuidSet (set[str], optional): 使用過的UUID. Defaults to set().

    Returns:
        str: UUID4_HEX
    """
    while True:
        u = uuid.uuid4().hex
        if u not in uuidSet:
            return u