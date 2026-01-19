# ui/styles.py

QSS_STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #f0f0f0;
    font-size: 16px;
    font-family: "Microsoft JhengHei", "Noto Sans TC", Arial;
}

/* ===== 按鈕 ===== */
QPushButton {
    background-color: #2b2b2b;
    color: #f0f0f0;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 16px;
    border: 1px solid #3a3a3a;
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #888888;
    border: 1px solid #2f2f2f;
}
QPushButton:hover:!disabled {
    background-color: #3d3d3d;
}
QPushButton:pressed {
    background-color: #333333;
}

/* ===== 清單、輸入框 ===== */
QListWidget {
    background: #232323;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    font-size: 15px;
    selection-background-color: #3d3d3d;
    selection-color: #ffffff;
}
QLineEdit, QTextEdit {
    background: #262626;
    color: #f0f0f0;
    border: 1px solid #3c3c3c;
    border-radius: 5px;
    font-size: 15px;
    padding: 4px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #5a5a5a;
}

/* ===== 標籤與群組框 ===== */
QLabel {
    font-size: 17px;
    font-weight: bold;
}
QGroupBox {
    border: 2px solid #3a3a3a;
    border-radius: 10px;
    margin-top: 12px;
    padding: 6px 6px 8px 6px;
    background-color: #1a1a1a;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #cccccc;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}

/* ===== 下拉選單與數值框 ===== */
QComboBox, QSpinBox, QDoubleSpinBox {
    background: #262626;
    color: #f0f0f0;
    border-radius: 5px;
    border: 1px solid #3c3c3c;
    font-size: 15px;
    padding: 4px 6px;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid #5a5a5a;
}

/* ===== 分頁標籤 ===== */
QTabBar::tab {
    background: #2b2b2b;
    color: #aaaaaa;
    padding: 6px 14px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #3d3d3d;
    color: #ffffff;
}
QTabBar::tab:hover {
    background: #333333;
    color: #ffffff;
}

/* ===== 額外按鈕樣式 ===== */
QPushButton#togglePasswordBtn {
    padding: 6px 12px;
    font-size: 16px;
    font-weight: bold;
    border-radius: 6px;
    background-color: #2b2b2b;
    border: 1px solid #3a3a3a;
}
QPushButton#togglePasswordBtn:hover {
    background-color: #3d3d3d;
}
"""
