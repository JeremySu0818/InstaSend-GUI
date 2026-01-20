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
        self.status_signal.emit("初始化 Instagram 客戶端...")
        try:
            if os.path.exists(session_file):
                self.status_signal.emit(f"嘗試載入 Session: {session_file}")
                self.cl.load_settings(session_file)
            self.status_signal.emit("登入中...")
            try:
                self.cl.login(username, password)
            except TwoFactorRequired:
                self.error_signal.emit(
                    "需要雙重驗證 (2FA)，請先關閉或手動登入一次生成 Session。"
                )
                self.end_signal.emit()
                return
            except ChallengeRequired:
                self.error_signal.emit(
                    "帳號觸發 Challenge 驗證，請手動登入 Web 版解決。"
                )
                self.end_signal.emit()
                return
            except BadPassword:
                self.error_signal.emit("密碼錯誤，請檢查設定。")
                self.end_signal.emit()
                return
            self.cl.dump_settings(session_file)
            self.status_signal.emit("登入成功，Session 已儲存。")
        except Exception as e:
            self.error_signal.emit(f"登入異常: {str(e)}")
            self.end_signal.emit()
            return
        self.status_signal.emit("解析目標...")
        target_info = self.resolve_target(target_input)
        if not target_info:
            self.error_signal.emit(f"無法解析目標: {target_input}")
            self.end_signal.emit()
            return
        target_id = target_info["id"]
        target_type = target_info["type"]
        self.status_signal.emit(f"目標 ({target_type}) ID: {target_id}")
        messages = [
            line
            for line in self.profile.get("message", "").splitlines()
            if line.strip()
        ]
        if not messages:
            self.error_signal.emit("訊息內容不得為空")
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
                self.status_signal.emit("狀態：暫停中")
                time.sleep(1)
                continue
            self.status_signal.emit("狀態：發送中...")
            msg_count += 1
            msg = messages[msg_index]
            msg_index = (msg_index + 1) % len(messages)
            try:
                self.cl.direct_send(msg, user_ids=[int(target_id)])
                self.status_signal.emit(f"發送第 {msg_count} 條訊息成功：{msg[:20]}...")
                if msg_count >= loop:
                    break
                if interval_mode == "fixed":
                    sec = interval
                else:
                    sec = random.uniform(interval_min, interval_max)
                self.status_signal.emit(f"等待 {sec:.1f} 秒...")
                slept = 0
                while slept < sec:
                    if self._stopped:
                        break
                    time.sleep(0.1)
                    slept += 0.1
            except FeedbackRequired:
                self.error_signal.emit(
                    "操作頻率過快，已被 Instagram 暫時限制 (Feedback Required)。"
                )
                break
            except PleaseWaitFewMinutes:
                self.error_signal.emit("操作過快，請稍候 (Please wait a few minutes)。")
                time.sleep(60)
            except Exception as e:
                self.error_signal.emit(f"發送失敗: {e}")
                break
        self.status_signal.emit("任務結束")
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
            self.error_signal.emit(f"解析用戶名失敗: {e}")
            return None
        return None

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._stopped = True
