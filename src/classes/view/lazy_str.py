#####
# 延遲翻譯字串符
#####
from PySide6.QtCore import QCoreApplication

class LazyStr():
    """延緩翻譯字符串
    """
    def __init__(self, text:str, context="XiaoYao"):
        self.context = context
        self.text = text

    def __str__(self):
        return QCoreApplication.translate(self.context, self.text)

    def __call__(self):
        return str(self)