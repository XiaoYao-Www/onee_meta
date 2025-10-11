from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt

class SmartHandleSplitter(QSplitter):
    def __init__(self, orientation):
        super().__init__(orientation)
        self.splitterMoved.connect(self.update_handle_style)
        self.setStyleSheet("""
                QSplitter::handle {
                    background-color: transparent;
                }
            """)

    def update_handle_style(self):
        sizes = self.sizes()
        
        if sizes[0] == 0 or sizes[1] == 0:
            # 到達極限 → 顯示抓手
            self.setStyleSheet("""
                QSplitter::handle {
                    image: url(assets/textures/splitter_handle.png);
                    background-repeat: no-repeat;
                    background-position: center;
                    border-radius: 4px;
                }
                QSplitter::handle:horizontal {
                    width: 3px;
                }
            """)
        else:
            # 還原樣式
            self.setStyleSheet("""
                QSplitter::handle {
                    background-color: transparent;
                    border-radius: 4px;
                }
                QSplitter::handle:horizontal {
                    width: 3px;
                }
            """)
        # if sizes[0] == 0 or sizes[1] == 0:
        #     # 到達極限 → 紅色
        #     self.setStyleSheet("""
        #         QSplitter::handle {
        #             background-color: red;
        #         }
        #         QSplitter::handle:horizontal {
        #             width: 8px;
        #         }
        #     """)
        # else:
        #     # 平常 → 灰色
        #     self.setStyleSheet("""
        #         QSplitter::handle {
        #             background-color: #888;
        #         }
        #         QSplitter::handle:horizontal {
        #             width: 4px;
        #         }
        #     """)
