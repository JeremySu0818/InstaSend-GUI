from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QGroupBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QIcon
from utils.system import resource_path
from ui.styles import QSS_STYLE
from ui.components import ProfileDialog
from core.worker import SendDMThread
from core.profile import ProfileData


class DMWindow(QWidget):
    STATUS_IDLE = 0
    STATUS_RUNNING = 1
    STATUS_PAUSED = 2
    STATUS_ENDED = 3

    _STATUS_LABELS = {
        STATUS_IDLE: "Status: Not Started",
        STATUS_RUNNING: "Status: Running",
        STATUS_PAUSED: "Status: Paused",
        STATUS_ENDED: "Status: Ended",
    }

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.setWindowTitle("InstaSend")
        self.setMinimumSize(QSize(650, 520))
        self.setStyleSheet(QSS_STYLE)

        main = QHBoxLayout(self)
        self.profile_list = QListWidget()
        self.profile_list.setFixedWidth(220)
        self.profile_list.itemDoubleClicked.connect(self.edit_profile)
        self.profile_list.currentRowChanged.connect(self._update_buttons)
        main.addWidget(self.profile_list, 1)

        right = QVBoxLayout()
        group_manage = QGroupBox("Account Management")
        manage_btns = QHBoxLayout()
        self.btn_new = QPushButton("Add")
        self.btn_edit = QPushButton("Edit")
        self.btn_del = QPushButton("Delete")
        manage_btns.addWidget(self.btn_new)
        manage_btns.addWidget(self.btn_edit)
        manage_btns.addWidget(self.btn_del)
        group_manage.setLayout(manage_btns)
        right.addWidget(group_manage)

        group_run = QGroupBox("Send Control")
        run_btns = QHBoxLayout()
        self.btn_send = QPushButton("Send")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.btn_stop = QPushButton("Stop")
        run_btns.addWidget(self.btn_send)
        run_btns.addWidget(self.btn_pause)
        run_btns.addWidget(self.btn_resume)
        run_btns.addWidget(self.btn_stop)
        group_run.setLayout(run_btns)
        right.addWidget(group_run)

        right.addSpacing(12)
        self.status_label = QLabel(self._STATUS_LABELS[self.STATUS_IDLE])
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(44)
        right.addWidget(self.status_label)
        right.addStretch()
        main.addLayout(right, 0)

        self.btn_new.clicked.connect(self.add_profile)
        self.btn_edit.clicked.connect(self.edit_profile)
        self.btn_del.clicked.connect(self.del_profile)
        self.btn_send.clicked.connect(self.start_dm)
        self.btn_pause.clicked.connect(self.pause_dm)
        self.btn_resume.clicked.connect(self.resume_dm)
        self.btn_stop.clicked.connect(self.stop_dm)

        self.settings = QSettings("MyCompany", "InstaSend")
        self.profile_names: list[str] = []
        self.active_thread: SendDMThread | None = None
        self.active_profile: ProfileData | None = None
        self._status = self.STATUS_IDLE
        self._refresh_profiles()
        self._update_buttons()



    def _change_status(self, new_status: int):
        self._status = new_status
        self.status_label.setText(self._STATUS_LABELS.get(new_status, "Status: Unknown"))
        self._update_buttons()

    def _update_buttons(self):
        has_sel = self.profile_list.currentRow() >= 0
        is_running = self._status == self.STATUS_RUNNING
        is_paused = self._status == self.STATUS_PAUSED
        self.btn_new.setEnabled(not is_running and not is_paused)
        self.btn_edit.setEnabled(has_sel and not is_running and not is_paused)
        self.btn_del.setEnabled(has_sel and not is_running and not is_paused)
        self.profile_list.setEnabled(not is_running and not is_paused)
        self.btn_send.setEnabled(has_sel and self._status == self.STATUS_IDLE)
        self.btn_pause.setEnabled(is_running)
        self.btn_resume.setEnabled(is_paused)
        self.btn_stop.setEnabled(is_running or is_paused)



    def _refresh_profiles(self):
        self.profile_list.clear()
        self.profile_names = sorted(self.settings.childGroups())
        for name in self.profile_names:
            self.settings.beginGroup(name)
            note = self.settings.value("dm_note", "")
            self.settings.endGroup()
            display = f"{name} ({note})" if note else name
            self.profile_list.addItem(display)
        self._update_buttons()

    def _get_selected_section(self) -> str | None:
        row = self.profile_list.currentRow()
        if 0 <= row < len(self.profile_names):
            return self.profile_names[row]
        return None

    def _load_profile(self, section: str) -> ProfileData:
        raw: dict = {}
        self.settings.beginGroup(section)
        for key in self.settings.childKeys():
            raw[key] = self.settings.value(key)
        self.settings.endGroup()
        raw["section"] = section
        return ProfileData.from_dict(raw)

    def _save_profile(self, profile: ProfileData):
        self.settings.beginGroup(profile.section)
        for key, value in profile.to_settings_dict().items():
            self.settings.setValue(key, value)
        self.settings.endGroup()



    def add_profile(self):
        dialog = ProfileDialog(self, title="Add Profile")
        if dialog.exec_():
            profile = dialog.get_profile()
            if profile.section in self.settings.childGroups():
                QMessageBox.warning(self, "Duplicate Name", "This profile name already exists.")
                return
            self._save_profile(profile)
            self._refresh_profiles()

    def edit_profile(self):
        section = self._get_selected_section()
        if not section:
            QMessageBox.information(self, "Please Select", "Please select a profile to edit.")
            return
        profile = self._load_profile(section)
        dialog = ProfileDialog(self, profile=profile, title="Edit Profile")
        if dialog.exec_():
            updated = dialog.get_profile()
            if updated.section != section:
                if updated.section in self.settings.childGroups():
                    QMessageBox.warning(self, "Duplicate Name", "The new name already exists.")
                    return
                self.settings.remove(section)
            self._save_profile(updated)
            self._refresh_profiles()

    def del_profile(self):
        section = self._get_selected_section()
        if not section:
            QMessageBox.information(self, "Please Select", "Please select a profile to delete.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete [{section}]?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings.remove(section)
            self._refresh_profiles()



    def start_dm(self):
        section = self._get_selected_section()
        if not section:
            QMessageBox.information(self, "Please Select", "Please select a profile to start.")
            return
        if self.active_thread and self.active_thread.isRunning():
            QMessageBox.warning(self, "Process Running", "Please stop the current process first.")
            return

        profile = self._load_profile(section)
        self.active_profile = profile
        self.active_thread = SendDMThread(profile)
        self.active_thread.status_signal.connect(self.status_label.setText)
        self.active_thread.error_signal.connect(self.status_label.setText)
        self.active_thread.end_signal.connect(self._on_thread_end)
        self.active_thread.start()
        self._change_status(self.STATUS_RUNNING)

    def pause_dm(self):
        if self.active_thread:
            self.active_thread.pause()
            self._change_status(self.STATUS_PAUSED)

    def resume_dm(self):
        if self.active_thread:
            self.active_thread.resume()
            self._change_status(self.STATUS_RUNNING)

    def stop_dm(self):
        if self.active_thread:
            self.active_thread.stop()
            self.active_thread.wait()
            self.active_thread = None
            self._change_status(self.STATUS_ENDED)

    def _on_thread_end(self):
        self.active_thread = None
        self._change_status(self.STATUS_IDLE)
