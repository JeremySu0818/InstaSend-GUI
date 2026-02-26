from PyQt5.QtCore import QThread, pyqtSignal
import time
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
    ClientError,
)
from utils.system import ensure_directory
from core.profile import ProfileData


class SendDMThread(QThread):
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    end_signal = pyqtSignal()

    def __init__(self, profile: ProfileData):
        super().__init__()
        self.profile = profile
        self._paused = False
        self._stopped = False
        self.cl = None
        self._session_file = ""

    def _login(self, session_file: str):
        self.cl = Client()
        self.cl.delay_range = [1, 3]
        username, password = self.profile.username, self.profile.password

        if os.path.exists(session_file):
            self.status_signal.emit(f"Loading session: {session_file}")
            try:
                self.cl.load_settings(session_file)
                self.cl.login(username, password)
                self.status_signal.emit("Validating session...")
                try:
                    self.cl.get_timeline_feed()
                    self.status_signal.emit("Session is valid.")
                except LoginRequired:
                    self.status_signal.emit(
                        "Session is invalid, re-logging in with saved device info..."
                    )
                    self._refresh_session(username, password)
                return
            except (TwoFactorRequired, ChallengeRequired, BadPassword):
                raise
            except Exception as e:
                self.status_signal.emit(
                    f"Session login failed ({e}), trying fresh login..."
                )


        self.status_signal.emit("Logging in with username and password...")
        self.cl.login(username, password)
        self.cl.dump_settings(session_file)
        self.status_signal.emit("Login successful. Session saved.")

    def _refresh_session(self, username: str, password: str):
        old_session = self.cl.get_settings()
        self.cl.set_settings({})
        self.cl.set_uuids(old_session["uuids"])
        self.cl.login(username, password)
        if self._session_file:
            self.cl.dump_settings(self._session_file)

    def _remove_session_file(self):
        if self._session_file and os.path.exists(self._session_file):
            try:
                os.remove(self._session_file)
                self.status_signal.emit("Removed invalid session file.")
            except Exception as e:
                self.status_signal.emit(f"Could not remove session file: {e}")

    def _send_message_with_retry(self, msg: str, target_id: int) -> bool:
        try:
            self.cl.direct_send(msg, user_ids=[target_id])
            return True
        except LoginRequired:
            self.status_signal.emit("Session expired during send. Re-logging in...")
            try:
                self._refresh_session(self.profile.username, self.profile.password)
                self.status_signal.emit("Re-login successful. Retrying send...")
                self.cl.direct_send(msg, user_ids=[target_id])
                return True
            except Exception as e:
                self.error_signal.emit(f"Re-login or retry failed: {e}")
                return False

    def _interruptible_sleep(self, seconds: float):
        end_time = time.time() + seconds
        while time.time() < end_time and not self._stopped:
            time.sleep(0.1)

    def run(self):
        p = self.profile
        session_folder = os.path.expandvars(
            os.path.join("%USERPROFILE%", "InstaSend", "sessions")
        )
        ensure_directory(session_folder)
        self._session_file = os.path.join(session_folder, f"{p.username}_session.json")

        self.status_signal.emit("Initializing Instagram client...")
        try:
            self._login(self._session_file)
        except TwoFactorRequired:
            self.error_signal.emit(
                "Two-Factor Authentication (2FA) required. "
                "Please disable it or log in manually once to generate a session."
            )
            self.end_signal.emit()
            return
        except ChallengeRequired:
            self._remove_session_file()
            self.error_signal.emit(
                "Account triggered challenge verification. "
                "Please log in via web/app to resolve, then try again."
            )
            self.end_signal.emit()
            return
        except BadPassword:
            self._remove_session_file()
            self.error_signal.emit("Incorrect password. Please check your settings.")
            self.end_signal.emit()
            return
        except Exception as e:
            self._remove_session_file()
            self.error_signal.emit(f"Login exception: {e}")
            self.end_signal.emit()
            return

        self.status_signal.emit("Resolving target...")
        target_id = self._resolve_target(p.target_user)
        if target_id is None:
            self.error_signal.emit(f"Failed to resolve target: {p.target_user}")
            self.end_signal.emit()
            return
        self.status_signal.emit(f"Target ID: {target_id}")

        messages = p.messages
        if not messages:
            self.error_signal.emit("Message content cannot be empty")
            self.end_signal.emit()
            return

        loop = p.loop_count
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
                if not self._send_message_with_retry(msg, target_id):
                    break
                self.status_signal.emit(
                    f"Successfully sent message #{msg_count}: {msg[:20]}..."
                )
                if msg_count >= loop:
                    break
                sec = p.get_delay()
                self.status_signal.emit(f"Waiting {sec:.1f}s...")
                self._interruptible_sleep(sec)
            except FeedbackRequired:
                self.error_signal.emit(
                    "Action frequency too high. "
                    "Temporarily restricted by Instagram (Feedback Required)."
                )
                break
            except PleaseWaitFewMinutes:
                self.error_signal.emit("Action too fast. Please wait a few minutes.")
                self._interruptible_sleep(60)
            except ClientError as e:
                self.error_signal.emit(f"Instagram API error: {e}")
                break
            except Exception as e:
                self.error_signal.emit(f"Failed to send: {e}")
                break

        self.status_signal.emit("Task ended")
        self.end_signal.emit()

    def _resolve_target(self, input_str: str) -> int | None:
        input_str = input_str.strip()
        if input_str.isdigit():
            return int(input_str)

        username = input_str
        if "instagram.com" in input_str:
            match = re.search(r"instagram\.com/([^/?#]+)", input_str)
            if match and match.group(1) != "direct":
                username = match.group(1)

        try:
            user_info = self.cl.user_info_by_username_v1(username)
            if user_info and user_info.pk:
                return int(user_info.pk)
        except Exception as e:
            self.error_signal.emit(f"Failed to resolve username: {e}")
        return None

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._stopped = True
