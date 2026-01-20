# ui/main_window.py

import time
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


class DMWindow(QWidget):
    STATUS_IDLE = 0
    STATUS_RUNNING = 1
    STATUS_PAUSED = 2
    STATUS_ENDED = 3

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.status = self.STATUS_IDLE
        self.setWindowTitle("InstaSend (Instagrapi Edition)")
        self.setMinimumSize(QSize(650, 520))
        self.setStyleSheet(QSS_STYLE)

        main = QHBoxLayout(self)
        self.profile_list = QListWidget()
        self.profile_list.setFixedWidth(220)
        self.profile_list.itemDoubleClicked.connect(self.edit_profile)
        self.profile_list.currentRowChanged.connect(self.update_buttons)
        main.addWidget(self.profile_list, 1)

        right = QVBoxLayout()
        group_manage = QGroupBox("帳號管理")
        manage_btns = QHBoxLayout()
        self.btn_new = QPushButton("新增")
        self.btn_edit = QPushButton("編輯")
        self.btn_del = QPushButton("刪除")
        manage_btns.addWidget(self.btn_new)
        manage_btns.addWidget(self.btn_edit)
        manage_btns.addWidget(self.btn_del)
        group_manage.setLayout(manage_btns)
        right.addWidget(group_manage)

        group_run = QGroupBox("發送控制")
        run_btns = QHBoxLayout()
        self.btn_send = QPushButton("發送")
        self.btn_pause = QPushButton("暫停")
        self.btn_resume = QPushButton("繼續")
        self.btn_stop = QPushButton("結束")
        run_btns.addWidget(self.btn_send)
        run_btns.addWidget(self.btn_pause)
        run_btns.addWidget(self.btn_resume)
        run_btns.addWidget(self.btn_stop)
        group_run.setLayout(run_btns)
        right.addWidget(group_run)

        right.addSpacing(12)
        self.status_label = QLabel("狀態：未啟動")
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
        self.profile_names = []
        self.refresh_profiles()
        self.active_thread = None
        self.active_profile = None
        self.status = self.STATUS_IDLE
        self.update_buttons()

    def refresh_profiles(self):
        self.profile_list.clear()
        self.profile_names = sorted(self.settings.childGroups())
        for name in self.profile_names:
            self.settings.beginGroup(name)
            note = self.settings.value("dm_note", "")
            self.settings.endGroup()
            display = name if not note else f"{name}（{note}）"
            self.profile_list.addItem(display)
        self.update_buttons()

    def get_selected_section(self):
        row = self.profile_list.currentRow()
        if 0 <= row < len(self.profile_names):
            return self.profile_names[row]
        return None

    def add_profile(self):
        dialog = ProfileDialog(self, title="新增設定檔")
        if dialog.exec_():
            d = dialog.get_profile()
            name = d["section"]
            if not all(
                [name, d["username"], d["password"], d["target_user"], d["message"]]
            ):
                QMessageBox.warning(self, "欄位不完整", "請輸入所有必填欄位。")
                return
            if name in self.settings.childGroups():
                QMessageBox.warning(self, "名稱重複", "此名稱已存在。")
                return
            self.settings.beginGroup(name)
            for key, value in d.items():
                if key != "section":
                    self.settings.setValue(key, value)
            self.settings.endGroup()
            self.refresh_profiles()

    def edit_profile(self):
        section = self.get_selected_section()
        if not section:
            QMessageBox.information(self, "請先選擇", "請點選要編輯的設定檔。")
            return
        profile_data = {}
        self.settings.beginGroup(section)
        for key in self.settings.childKeys():
            profile_data[key] = self.settings.value(key)
        self.settings.endGroup()
        profile_data["section"] = section
        dialog = ProfileDialog(self, profile_data=profile_data, title="編輯設定檔")
        if dialog.exec_():
            d2 = dialog.get_profile()
            new_section = d2["section"]
            if not all(
                [
                    new_section,
                    d2["username"],
                    d2["password"],
                    d2["username"],
                    d2["password"],
                    d2["target_user"],
                    d2["message"],
                ]
            ):
                QMessageBox.warning(self, "欄位不完整", "請輸入所有必填欄位。")
                return
            if new_section != section:
                if new_section in self.settings.childGroups():
                    QMessageBox.warning(self, "名稱重複", "新的名稱已存在。")
                    return
                self.settings.remove(section)
            self.settings.beginGroup(new_section)
            for key, value in d2.items():
                if key != "section":
                    self.settings.setValue(key, value)
            self.settings.endGroup()
            self.refresh_profiles()

    def del_profile(self):
        section = self.get_selected_section()
        if not section:
            QMessageBox.information(self, "請先選擇", "請點選要刪除的設定檔。")
            return
        reply = QMessageBox.question(
            self,
            "確定刪除",
            f"確定要刪除 [{section}] 嗎？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings.remove(section)
            self.refresh_profiles()

    def start_dm(self):
        section = self.get_selected_section()
        if not section:
            QMessageBox.information(self, "請先選擇", "請點選一個設定檔啟動。")
            return
        if self.active_thread and self.active_thread.isRunning():
            QMessageBox.warning(self, "進程已啟動", "請先停止現有進程。")
            return
        profile_data = {}
        self.settings.beginGroup(section)
        for key in self.settings.childKeys():
            profile_data[key] = self.settings.value(key)
        self.settings.endGroup()
        self.active_profile = profile_data
        self.active_thread = SendDMThread(profile_data)
        self.active_thread.status_signal.connect(self.status_label.setText)
        self.active_thread.error_signal.connect(self.status_label.setText)
        self.active_thread.end_signal.connect(self.on_thread_end)
        self.active_thread.start()
        self.status = self.STATUS_RUNNING
        self.update_buttons()
        self.status_label.setText("狀態：運行中")

    def pause_dm(self):
        if self.active_thread:
            self.active_thread.pause()
            self.status = self.STATUS_PAUSED
            self.update_buttons()
            self.status_label.setText("狀態：暫停中")

    def resume_dm(self):
        if self.active_thread:
            self.active_thread.resume()
            self.status = self.STATUS_RUNNING
            self.update_buttons()
            self.status_label.setText("狀態：運行中")

    def stop_dm(self):
        if self.active_thread:
            self.active_thread.stop()
            self.active_thread.wait()
            self.active_thread = None
            self.status = self.STATUS_ENDED
            self.update_buttons()
            self.status_label.setText("狀態：已結束")

    def on_thread_end(self):
        self.active_thread = None
        self.status = self.STATUS_IDLE
        self.update_buttons()
        self.status_label.setText("狀態：已結束")

    def update_buttons(self):
        has_sel = self.profile_list.currentRow() >= 0
        is_running = self.status == self.STATUS_RUNNING
        is_paused = self.status == self.STATUS_PAUSED
        self.btn_new.setEnabled(not is_running and not is_paused)
        self.btn_edit.setEnabled(has_sel and not is_running and not is_paused)
        self.btn_del.setEnabled(has_sel and not is_running and not is_paused)
        self.profile_list.setEnabled(not is_running and not is_paused)
        self.btn_send.setEnabled(has_sel and self.status == self.STATUS_IDLE)
        self.btn_pause.setEnabled(is_running)
        self.btn_resume.setEnabled(is_paused)
        self.btn_stop.setEnabled(is_running or is_paused)
