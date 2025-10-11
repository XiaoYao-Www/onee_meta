#####
# 執行時數據儲存類
#####
import threading
from typing import Any, Dict, Optional, Set, Callable, TypeVar

T = TypeVar('T')

class DataStore:
    """ 數據存儲類
        ※ 取得的資料並非副本，修改須謹慎 
    """
    
    def __init__(self, id: Optional[str] = None):
        self._id : Optional[str] = id
        self._data: Dict[str, Any] = {}
        self._mutex = threading.Lock()
        self._callbacks: Set[Callable[[Dict[str, Any], Optional[str]], None]] = set()
    
    @property
    def data(self) -> Dict[str, Any]:
        """獲取全部資料

        Returns:
            Dict[str, Any]: 資料結構(資料名, 資料)
        """
        with self._mutex:
            return self._data
        
    @property
    def id(self) -> Optional[str]:
        """獲取容器ID

        Returns:
            Optional[str]: ID
        """
        return self._id
    
    def subscribe(self, callback: Callable[[Dict[str, Any], Optional[str]], None]) -> None:
        """訂閱數據變更
            回掉函式結構 :
                callback(變動資料字典, 容器id)

        Args:
            callback (Callable[[Dict[str, Any], Optional[str]], None]): 回調函數
        """
        with self._mutex:
            self._callbacks.add(callback)
    
    def unsubscribe(self, callback: Callable[[Dict[str, Any], Optional[str]], None]) -> None:
        """取消訂閱

        Args:
            callback (Callable[[Dict[str, Any], Optional[str]], None]): 目標函數
        """
        with self._mutex:
            self._callbacks.discard(callback)
    
    def _notify(self, changes: Dict[str, Any]) -> None:
        """內部通知機制

        Args:
            changes (Dict[str, Any]): 變動資料
        """
        with self._mutex:
            callbacks = self._callbacks.copy()
        for callback in callbacks:
            try:
                callback(changes, self._id)
            except Exception:
                import traceback
                print(f"[DataStore:{self._id}] 回調錯誤，鍵: {list(changes.keys())}")
                traceback.print_exc()
    
    def update(self, new_data: Dict[str, Any]) -> None:
        """批量更新數據
            若資料實際變更才通知

        Args:
            new_data (Dict[str, Any]): 改變的資料
        """
        changed = {}
        with self._mutex:
            for key, new_value in new_data.items():
                old_value = self._data.get(key)
                if old_value != new_value:
                    self._data[key] = new_value
                    changed[key] = new_value
        if changed:
            self._notify(changed)
    
    def get(self, key: str, default: Optional[T] = None) -> T:
        """獲取單個值

        Args:
            key (str): 鍵
            default (Optional[T], optional): 預設值. Defaults to None.

        Returns:
            T: 值
        """
        with self._mutex:
            return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """設置單個值
            若資料實際變更才通知

        Args:
            key (str): 鍵
            value (Any): 值
        """
        with self._mutex:
            old_value = self._data.get(key)
            if old_value == value:
                return
            self._data[key] = value
        self._notify({key: value})
    
    def clear(self) -> None:
        """清空所有數據
        """
        with self._mutex:
            if not self._data:
                return
            self._data.clear()
        self._notify({})