# core/worker.py
from PyQt5.QtCore import QThread, pyqtSignal
import time
import random
import os
import re
from urllib.parse import urlparse
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    FeedbackRequired,
    PleaseWaitFewMinutes,
    BadPassword,
)
from utils.system import ensure_directory


class SendDMThread(QThread):
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    end_signal = pyqtSignal()

    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self._paused = False
        self._stopped = False
        self.cl = None

    def run(self):
        username = self.profile["username"]
        password = self.profile["password"]
        target_input = self.profile.get("target_user", "")
        session_folder = os.path.expandvars(
            os.path.join("%USERPROFILE%", "InstaSend", "sessions")
        )
        ensure_directory(session_folder)
        session_file = os.path.join(session_folder, f"{username}_session.json")
        self.cl = Client()
        self.status_signal.emit("Initializing Instagram client...")
        try:
            if os.path.exists(session_file):
                self.status_signal.emit(f"Trying to load Session: {session_file}")
                self.cl.load_settings(session_file)
            self.status_signal.emit("Logging in...")
            try:
                self.cl.login(username, password)
            except TwoFactorRequired:
                self.error_signal.emit(
                    "Two-Factor Authentication (2FA) required. Please disable it or log in manually once to generate a session."
                )
                self.end_signal.emit()
                return
            except ChallengeRequired:
                self.error_signal.emit(
                    "Account triggered challenge verification. Please log in via web to resolve."
                )
                self.end_signal.emit()
                return
            except BadPassword:
                self.error_signal.emit("Incorrect password. Please check your settings.")
                self.end_signal.emit()
                return
            self.cl.dump_settings(session_file)
            self.status_signal.emit("Login successful. Session saved.")
        except Exception as e:
            self.error_signal.emit(f"Login exception: {str(e)}")
            self.end_signal.emit()
            return
        self.status_signal.emit("Resolving target...")
        target_info = self.resolve_target(target_input)
        if not target_info:
            self.error_signal.emit(f"Failed to resolve target: {target_input}")
            self.end_signal.emit()
            return
        target_id = target_info["id"]
        target_type = target_info["type"]
        self.status_signal.emit(f"Target ({target_type}) ID: {target_id}")
        messages = [
            line
            for line in self.profile.get("message", "").splitlines()
            if line.strip()
        ]
        if not messages:
            self.error_signal.emit("Message content cannot be empty")
            self.end_signal.emit()
            return
        if self.profile.get("send_mode", "single") == "single":
            messages = [messages[0]]
        mode = self.profile.get("send_mode", "single")
        interval_mode = self.profile.get("interval_mode", "fixed")
        interval = float(self.profile.get("send_interval", "0"))
        interval_min = float(self.profile.get("send_interval_min", "0"))
        interval_max = float(self.profile.get("send_interval_max", "0"))
        count = int(self.profile.get("send_count", "1") or "1")
        if mode == "single":
            loop = 1
        elif mode == "multi":
            loop = count
        elif mode == "infinite":
            loop = float("inf")
        else:
            loop = 1
        msg_index = 0
        msg_count = 0
        while not self._stopped and msg_count < loop:
            if self._paused:
                self.status_signal.emit("Status: Paused")
                time.sleep(1)
                continue
            self.status_signal.emit("Status: Sending...")
            msg_count += 1
            msg = messages[msg_index]
            msg_index = (msg_index + 1) % len(messages)
            try:
                self.cl.direct_send(msg, user_ids=[int(target_id)])
                self.status_signal.emit(f"Successfully sent message #{msg_count}: {msg[:20]}...")
                if msg_count >= loop:
                    break
                if interval_mode == "fixed":
                    sec = interval
                else:
                    sec = random.uniform(interval_min, interval_max)
                self.status_signal.emit(f"Waiting {sec:.1f}s...")
                slept = 0
                while slept < sec:
                    if self._stopped:
                        break
                    time.sleep(0.1)
                    slept += 0.1
            except FeedbackRequired:
                self.error_signal.emit(
                    "Action frequency too high. Temporarily restricted by Instagram (Feedback Required)."
                )
                break
            except PleaseWaitFewMinutes:
                self.error_signal.emit("Action too fast. Please wait a few minutes.")
                time.sleep(60)
            except Exception as e:
                self.error_signal.emit(f"Failed to send: {e}")
                break
        self.status_signal.emit("Task ended")
        self.end_signal.emit()

    def resolve_target(self, input_str):
        input_str = input_str.strip()
        if input_str.isdigit():
            return {"type": "user", "id": int(input_str)}
        username = input_str
        if "instagram.com" in input_str:
            try:
                parsed = urlparse(input_str)
                path_parts = [p for p in parsed.path.strip("/").split("/") if p]
                if path_parts and "direct" not in path_parts:
                    username = path_parts[0]
            except:
                pass
        try:
            user_info = self.cl.user_info_by_username_v1(username)
            if user_info and user_info.pk:
                return {"type": "user", "id": int(user_info.pk)}
        except Exception as e:
            self.error_signal.emit(f"Failed to resolve username: {e}")
            return None
        return None

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._stopped = True
