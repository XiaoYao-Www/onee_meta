from PySide6.QtWidgets import QVBoxLayout, QFrame, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

from src.classes.view.widgets.clickable_label import ClickableLabel


# ==========================================
# 2. 單筆資料的「卡片」元件
# ==========================================
class DataCard(QFrame):
    element_clicked = Signal(str, str)

    def __init__(self, data_dict, parent=None):
        super().__init__(parent)
        
        # 設定卡片的外觀（邊框、背景、圓角），這能明顯區隔每一筆資料
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        
        # 定義我們要顯示的普通文字欄位
        text_fields = ['Title', 'Author(s)', 'Publisher', 'Languages', 'Identifiers']
        
        for field in text_fields:
            if field in data_dict:
                # 使用自訂的 ClickableLabel
                lbl = ClickableLabel(field, data_dict[field])
                lbl.clicked.connect(self.on_element_clicked)
                layout.addWidget(lbl)

        # 針對 Tags 進行特殊處理（分割字串並做成按鈕網格）
        if 'Tags' in data_dict and data_dict['Tags']:
            tags_layout = QGridLayout()
            tags_label = ClickableLabel("Tag", data_dict["Tags"], "<b>Tags:</b>")
            tags_label.clicked.connect(self.on_element_clicked)
            layout.addWidget(tags_label)
            
            # 將 Tags 以逗號分割
            tags_list = [t.strip() for t in data_dict['Tags'].split(',')]
            
            row, col = 0, 0
            max_columns = 5 # 每行最多顯示 5 個 Tag
            
            for tag in tags_list:
                if not tag: continue
                
                # 將每個 Tag 做成按鈕
                btn = QPushButton(tag)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # 這裡使用 lambda 綁定特定值，注意 t=tag 是為了避免閉包(closure)變數覆蓋問題
                btn.clicked.connect(lambda checked=False, t=tag: self.on_element_clicked("Tag", t))
                
                tags_layout.addWidget(btn, row, col)
                
                # 計算下一個 Tag 要放的網格位置
                col += 1
                if col >= max_columns:
                    col = 0
                    row += 1
                    
            layout.addLayout(tags_layout)

    def on_element_clicked(self, field, value):
        # 統一處理卡片內所有元素的點擊事件
        self.element_clicked.emit(field, value)