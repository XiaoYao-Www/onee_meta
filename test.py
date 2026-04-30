import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QScrollArea,
                               QLabel, QFrame, QGridLayout, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt, Signal
from src.classes.calibre_scanner import CalibreSidecar

# ==========================================
# 1. 自訂可點擊的 Label
# ==========================================
class ClickableLabel(QLabel):
    # 定義一個訊號，當被點擊時發送 (欄位名稱, 內容值)
    clicked = Signal(str, str)

    def __init__(self, field_name, text_value, parent=None):
        super().__init__(f"<b>{field_name}:</b> {text_value}", parent)
        self.field_name = field_name
        self.text_value = text_value
        
        # 讓滑鼠游標移過去時變成手指形狀
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # 設定基本的 Hover 效果
        # self.setStyleSheet("""
        #     QLabel { padding: 4px; border-radius: 4px; }
        #     QLabel:hover { background-color: #e0e6ed; color: #0056b3; }
        # """)

    def mouseReleaseEvent(self, event):
        # 當滑鼠放開時，觸發 clicked 訊號
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.field_name, self.text_value)
        super().mouseReleaseEvent(event)


# ==========================================
# 2. 單筆資料的「卡片」元件
# ==========================================
class DataCard(QFrame):
    def __init__(self, data_dict, parent=None):
        super().__init__(parent)
        
        # 設定卡片的外觀（邊框、背景、圓角），這能明顯區隔每一筆資料
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # self.setStyleSheet("""
        #     DataCard {
        #         background-color: #ffffff;
        #         border: 2px solid #cccccc;
        #         border-radius: 8px;
        #         margin-bottom: 10px;
        #     }
        # """)
        
        layout = QVBoxLayout(self)
        
        # 定義我們要顯示的普通文字欄位
        text_fields = ['Title', 'Author(s)', 'Publisher', 'Rating', 'Languages', 'Identifiers']
        
        for field in text_fields:
            if field in data_dict:
                # 使用自訂的 ClickableLabel
                lbl = ClickableLabel(field, data_dict[field])
                lbl.clicked.connect(self.on_element_clicked)
                layout.addWidget(lbl)

        # 針對 Tags 進行特殊處理（分割字串並做成按鈕網格）
        if 'Tags' in data_dict and data_dict['Tags']:
            tags_layout = QGridLayout()
            tags_label = QLabel("<b>Tags:</b>")
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
                # btn.setStyleSheet("""
                #     QPushButton {
                #         background-color: #f0f0f0;
                #         border: 1px solid #dcdcdc;
                #         border-radius: 10px;
                #         padding: 4px 8px;
                #     }
                #     QPushButton:hover {
                #         background-color: #d0e4ff;
                #         border: 1px solid #80b3ff;
                #     }
                # """)
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
        print(f"👉 你點擊了 [{field}] : {value}")


# ==========================================
# 3. 主視窗與滾動列表容器
# ==========================================
class MainApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("動態資料滾動列表")
        self.resize(800, 600)
        # self.setStyleSheet("background-color: #f4f5f7;") # 視窗底色設為淺灰，凸顯白色卡片
        
        main_layout = QVBoxLayout(self)

        # 建立控制列 (放置刷新按鈕)
        control_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新資料 (載入測試資料)")
        self.btn_refresh.setMinimumHeight(40)
        self.btn_clear = QPushButton("清空畫面")
        self.btn_clear.setMinimumHeight(40)
        
        control_layout.addWidget(self.btn_refresh)
        control_layout.addWidget(self.btn_clear)
        main_layout.addLayout(control_layout)

        # 建立滾動區域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # 允許內部元件縮放
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 建立滾動內容容器
        self.scroll_content = QWidget()
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # 讓項目靠上排列
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # 綁定按鈕事件
        self.btn_refresh.clicked.connect(self.load_sample_data)
        self.btn_clear.clicked.connect(self.clear_data)

    def clear_data(self):
        """ 清空目前列表中的所有資料卡片 """
        # 反向迴圈刪除 Layout 中的 Widget
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_list(self, data_list):
        """ 刷新函數：清空舊資料並載入新資料 """
        self.clear_data()
        
        # 逐筆建立資料卡片並加入佈局
        for item in data_list:
            card = DataCard(item)
            self.content_layout.addWidget(card)

    def load_sample_data(self):
        """ 測試用：注入你提供的 JSON 結構資料 """
        scanner = CalibreSidecar(r"C:\no_installation_required\Calibre Portable\Calibre")

        raw_data = scanner.fetch_metadata(
            title="Author(s)'",
        )

        self.update_list(raw_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())