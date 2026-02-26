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
from core.profile import ProfileData, SEND_MODES, INTERVAL_MODES


class ProfileDialog(QDialog):
    def __init__(self, parent=None, profile: ProfileData | None = None, title="Edit Profile"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 500)

        self.tabs = QTabWidget(self)
        self.tab_basic = QWidget()
        self.tab_message = QWidget()
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_basic, "Basic Info")
        self.tabs.addTab(self.tab_message, "Messages")
        self.tabs.addTab(self.tab_settings, "Settings")


        layout_basic = QFormLayout()
        self.edit_name = QLineEdit()
        self.edit_username = QLineEdit()
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)

        self.toggle_password_btn = QPushButton("Show")
        self.toggle_password_btn.setObjectName("togglePasswordBtn")
        self.toggle_password_btn.setMinimumWidth(80)
        self.toggle_password_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_password_btn.clicked.connect(self._toggle_password)

        self.edit_target = QLineEdit()
        self.edit_note = QLineEdit()
        pw_layout = QHBoxLayout()
        pw_layout.setSpacing(8)
        pw_layout.addWidget(self.edit_password, 1)
        pw_layout.addWidget(self.toggle_password_btn, 0)
        layout_basic.addRow("Profile Name *", self.edit_name)
        layout_basic.addRow("Instagram Username *", self.edit_username)
        layout_basic.addRow("Instagram Password *", pw_layout)
        layout_basic.addRow("Target User (User ID) *", self.edit_target)
        layout_basic.addRow("Notes", self.edit_note)
        self.tab_basic.setLayout(layout_basic)


        layout_msg = QVBoxLayout()
        self.edit_message = QTextEdit()
        self.edit_message.setPlaceholderText(
            "Please enter messages (one per line, will cycle through)"
        )
        self.edit_message.setFixedHeight(200)
        layout_msg.addWidget(self.edit_message)
        self.tab_message.setLayout(layout_msg)


        layout_send = QFormLayout()
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Send Single", "Send Multiple", "Infinite Send"])
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 9999)
        self.combo_interval_mode = QComboBox()
        self.combo_interval_mode.addItems(["Fixed Interval", "Random Interval"])
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(0, 3600)
        self.spin_interval.setSuffix("s")
        self.spin_interval.setSingleStep(0.5)
        self.spin_interval_min = QDoubleSpinBox()
        self.spin_interval_min.setRange(0, 3600)
        self.spin_interval_min.setSuffix("s")
        self.spin_interval_min.setSingleStep(0.5)
        self.spin_interval_max = QDoubleSpinBox()
        self.spin_interval_max.setRange(0, 3600)
        self.spin_interval_max.setSuffix("s")
        self.spin_interval_max.setSingleStep(0.5)
        layout_send.addRow("Send Mode *", self.combo_mode)
        layout_send.addRow("Send Count", self.spin_count)
        layout_send.addRow("Interval Mode *", self.combo_interval_mode)
        layout_send.addRow("Fixed Interval", self.spin_interval)
        layout_send.addRow("Min Interval", self.spin_interval_min)
        layout_send.addRow("Max Interval", self.spin_interval_max)
        self.tab_settings.setLayout(layout_send)


        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        self.combo_mode.currentIndexChanged.connect(self._on_mode_change)
        self.combo_interval_mode.currentIndexChanged.connect(self._on_interval_mode_change)
        self._on_mode_change()
        self._on_interval_mode_change()

        if profile:
            self._load_profile(profile)



    def _toggle_password(self):
        if self.edit_password.echoMode() == QLineEdit.Password:
            self.edit_password.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("Hide")
        else:
            self.edit_password.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("Show")

    def _set_row_visible(self, widget, visible: bool):
        widget.setVisible(visible)
        label = self.tab_settings.layout().labelForField(widget)
        if label:
            label.setVisible(visible)

    def _on_mode_change(self):
        mode_index = self.combo_mode.currentIndex()
        self._set_row_visible(self.spin_count, mode_index == 1)

        show_interval = mode_index != 0
        self._set_row_visible(self.combo_interval_mode, show_interval)
        self._on_interval_mode_change()

    def _on_interval_mode_change(self):
        mode_index = self.combo_mode.currentIndex()
        if mode_index == 0:
            for w in [self.spin_interval, self.spin_interval_min, self.spin_interval_max]:
                self._set_row_visible(w, False)
            return

        is_fixed = self.combo_interval_mode.currentIndex() == 0
        self._set_row_visible(self.spin_interval, is_fixed)
        self._set_row_visible(self.spin_interval_min, not is_fixed)
        self._set_row_visible(self.spin_interval_max, not is_fixed)

    def _on_accept(self):
        profile = self.get_profile()
        if not profile.validate_required():
            QMessageBox.warning(
                self, "Incomplete Fields", "Please fill in all required fields."
            )
            return

        if profile.send_mode == "single" and "\n" in profile.message:
            QMessageBox.warning(
                self,
                "Hint",
                "You selected 'Send Single' mode, but entered multiple lines.\n\n"
                "The system will only send the first line.",
            )

        self.accept()

    def _load_profile(self, p: ProfileData):
        self.edit_name.setText(p.section)
        self.edit_username.setText(p.username)
        self.edit_password.setText(p.password)
        self.edit_target.setText(p.target_user)
        self.edit_note.setText(p.dm_note)
        self.edit_message.setPlainText(p.message)

        self.combo_mode.setCurrentIndex(p.send_mode_index)
        self.spin_count.setValue(p.send_count)
        self.combo_interval_mode.setCurrentIndex(p.interval_mode_index)
        self.spin_interval.setValue(p.send_interval)
        self.spin_interval_min.setValue(p.send_interval_min)
        self.spin_interval_max.setValue(p.send_interval_max)



    def get_profile(self) -> ProfileData:
        return ProfileData(
            section=self.edit_name.text().strip(),
            username=self.edit_username.text().strip(),
            password=self.edit_password.text().strip(),
            target_user=self.edit_target.text().strip(),
            dm_note=self.edit_note.text().strip(),
            message=self.edit_message.toPlainText().strip(),
            send_mode=SEND_MODES[self.combo_mode.currentIndex()],
            send_count=self.spin_count.value() if self.combo_mode.currentIndex() == 1 else 1,
            interval_mode=INTERVAL_MODES[self.combo_interval_mode.currentIndex()],
            send_interval=self.spin_interval.value(),
            send_interval_min=self.spin_interval_min.value(),
            send_interval_max=self.spin_interval_max.value(),
        )
