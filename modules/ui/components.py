# ui/components.py
from PyQt5.QtWidgets import (
    QDialog,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QMessageBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt


class ProfileDialog(QDialog):
    def __init__(self, parent=None, profile_data=None, title="編輯設定檔"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 500)

        self.tabs = QTabWidget(self)
        self.tab_basic = QWidget()
        self.tab_message = QWidget()
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_basic, "基本資料")
        self.tabs.addTab(self.tab_message, "發送訊息")
        self.tabs.addTab(self.tab_settings, "發送設定")

        layout_basic = QFormLayout()
        self.edit_name = QLineEdit()
        self.edit_username = QLineEdit()
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)

        self.toggle_password_btn = QPushButton("顯示")
        self.toggle_password_btn.setObjectName("togglePasswordBtn")
        self.toggle_password_btn.setMinimumWidth(80)
        self.toggle_password_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_password_btn.clicked.connect(self.toggle_password)

        self.edit_target = QLineEdit()
        self.edit_note = QLineEdit()
        pw_layout = QHBoxLayout()
        pw_layout.setSpacing(8)
        pw_layout.addWidget(self.edit_password, 1)
        pw_layout.addWidget(self.toggle_password_btn, 0)
        layout_basic.addRow("設定檔名稱 *", self.edit_name)
        layout_basic.addRow("Instagram 帳號 *", self.edit_username)
        layout_basic.addRow("Instagram 密碼 *", pw_layout)
        layout_basic.addRow("目標用戶 (User ID) *", self.edit_target)
        layout_basic.addRow("備註說明", self.edit_note)
        self.tab_basic.setLayout(layout_basic)

        layout_msg = QVBoxLayout()
        self.edit_message = QTextEdit()
        self.edit_message.setPlaceholderText("請輸入要發送的訊息（多行可循環發送）")
        self.edit_message.setFixedHeight(200)
        layout_msg.addWidget(self.edit_message)
        self.tab_message.setLayout(layout_msg)

        layout_send = QFormLayout()
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["發送單條", "發送多條", "無限發送"])
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 9999)
        self.combo_interval_mode = QComboBox()
        self.combo_interval_mode.addItems(["固定間隔", "亂數間隔"])
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(0, 3600)
        self.spin_interval.setSuffix("秒")
        self.spin_interval.setSingleStep(0.5)
        self.spin_interval_min = QDoubleSpinBox()
        self.spin_interval_min.setRange(0, 3600)
        self.spin_interval_min.setSuffix("秒")
        self.spin_interval_min.setSingleStep(0.5)
        self.spin_interval_max = QDoubleSpinBox()
        self.spin_interval_max.setRange(0, 3600)
        self.spin_interval_max.setSuffix("秒")
        self.spin_interval_max.setSingleStep(0.5)
        layout_send.addRow("發送模式 *", self.combo_mode)
        layout_send.addRow("發送條數", self.spin_count)
        layout_send.addRow("間隔模式 *", self.combo_interval_mode)
        layout_send.addRow("固定間隔", self.spin_interval)
        layout_send.addRow("最小間隔", self.spin_interval_min)
        layout_send.addRow("最大間隔", self.spin_interval_max)
        self.tab_settings.setLayout(layout_send)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        self.combo_mode.currentIndexChanged.connect(self.on_mode_change)
        self.combo_interval_mode.currentIndexChanged.connect(
            self.on_interval_mode_change
        )
        self.on_mode_change()
        self.on_interval_mode_change()

        if profile_data:
            self.load_profile(profile_data)

    def toggle_password(self):
        if self.edit_password.echoMode() == QLineEdit.Password:
            self.edit_password.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("隱藏")
        else:
            self.edit_password.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("顯示")

    def on_mode_change(self):
        mode_index = self.combo_mode.currentIndex()
        show_count = mode_index == 1
        self.spin_count.setVisible(show_count)
        label = self.tab_settings.layout().labelForField(self.spin_count)
        if label:
            label.setVisible(show_count)

        show_interval = mode_index != 0
        self.combo_interval_mode.setVisible(show_interval)
        label = self.tab_settings.layout().labelForField(self.combo_interval_mode)
        if label:
            label.setVisible(show_interval)
        self.on_interval_mode_change()

    def on_interval_mode_change(self):
        mode_index = self.combo_mode.currentIndex()
        if mode_index == 0:
            for w in [
                self.spin_interval,
                self.spin_interval_min,
                self.spin_interval_max,
            ]:
                w.setVisible(False)
                label = self.tab_settings.layout().labelForField(w)
                if label:
                    label.setVisible(False)
            return

        is_fixed = self.combo_interval_mode.currentIndex() == 0
        self.spin_interval.setVisible(is_fixed)
        self.spin_interval_min.setVisible(not is_fixed)
        self.spin_interval_max.setVisible(not is_fixed)

        for w, visible in [
            (self.spin_interval, is_fixed),
            (self.spin_interval_min, not is_fixed),
            (self.spin_interval_max, not is_fixed),
        ]:
            label = self.tab_settings.layout().labelForField(w)
            if label:
                label.setVisible(visible)

    def load_profile(self, p):
        SEND_MODES = ["single", "multi", "infinite"]
        INTERVAL_MODES = ["fixed", "random"]
        mode_map = {
            "fixed_count": "multi",
            "single": "single",
            "multi": "multi",
            "infinite": "infinite",
        }
        mode = mode_map.get(p.get("send_mode", "single"), "single")
        interval = (
            p.get("interval_mode", "fixed")
            if p.get("interval_mode", "fixed") in INTERVAL_MODES
            else "fixed"
        )

        self.edit_name.setText(p.get("section", ""))
        self.edit_username.setText(p.get("username", ""))
        self.edit_password.setText(p.get("password", ""))
        self.edit_target.setText(p.get("target_user", ""))
        self.edit_note.setText(p.get("dm_note", ""))
        self.edit_message.setPlainText(p.get("message", ""))

        self.combo_mode.setCurrentIndex(SEND_MODES.index(mode))
        self.spin_count.setValue(int(p.get("send_count", 1)))
        self.combo_interval_mode.setCurrentIndex(INTERVAL_MODES.index(interval))
        self.spin_interval.setValue(float(p.get("send_interval", 0)))
        self.spin_interval_min.setValue(float(p.get("send_interval_min", 0)))
        self.spin_interval_max.setValue(float(p.get("send_interval_max", 0)))

    def get_profile(self):
        mode_val = ["single", "multi", "infinite"][self.combo_mode.currentIndex()]
        interval_mode_val = ["fixed", "random"][self.combo_interval_mode.currentIndex()]
        message_text = self.edit_message.toPlainText().strip()

        if mode_val == "single" and "\n" in message_text:
            QMessageBox.warning(
                self,
                "提示",
                "您選擇的是『發送單條』模式，但輸入了多行訊息。\n\n系統將只會發送第一行。",
            )

        return {
            "section": self.edit_name.text().strip(),
            "username": self.edit_username.text().strip(),
            "password": self.edit_password.text().strip(),
            "target_user": self.edit_target.text().strip(),
            "dm_note": self.edit_note.text().strip(),
            "message": message_text,
            "send_mode": mode_val,
            "send_count": self.spin_count.value() if mode_val == "multi" else 1,
            "interval_mode": interval_mode_val,
            "send_interval": self.spin_interval.value(),
            "send_interval_min": self.spin_interval_min.value(),
            "send_interval_max": self.spin_interval_max.value(),
        }
