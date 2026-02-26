from dataclasses import dataclass, field


SEND_MODES = ["single", "multi", "infinite"]
INTERVAL_MODES = ["fixed", "random"]

_MODE_COMPAT = {
    "fixed_count": "multi",
    "single": "single",
    "multi": "multi",
    "infinite": "infinite",
}


@dataclass
class ProfileData:
    section: str = ""
    username: str = ""
    password: str = ""
    target_user: str = ""
    dm_note: str = ""
    message: str = ""
    send_mode: str = "single"
    send_count: int = 1
    interval_mode: str = "fixed"
    send_interval: float = 0.0
    send_interval_min: float = 0.0
    send_interval_max: float = 0.0

    @property
    def loop_count(self) -> float:
        if self.send_mode == "single":
            return 1
        if self.send_mode == "multi":
            return self.send_count
        return float("inf")

    @property
    def messages(self) -> list[str]:
        lines = [l for l in self.message.splitlines() if l.strip()]
        if not lines:
            return []
        if self.send_mode == "single":
            return [lines[0]]
        return lines

    @property
    def send_mode_index(self) -> int:
        return SEND_MODES.index(self.send_mode) if self.send_mode in SEND_MODES else 0

    @property
    def interval_mode_index(self) -> int:
        return INTERVAL_MODES.index(self.interval_mode) if self.interval_mode in INTERVAL_MODES else 0

    def get_delay(self) -> float:
        if self.interval_mode == "fixed":
            return self.send_interval
        import random
        return random.uniform(self.send_interval_min, self.send_interval_max)

    @classmethod
    def from_dict(cls, d: dict) -> "ProfileData":
        raw_mode = str(d.get("send_mode", "single"))
        mode = _MODE_COMPAT.get(raw_mode, "single")

        raw_interval = str(d.get("interval_mode", "fixed"))
        interval = raw_interval if raw_interval in INTERVAL_MODES else "fixed"

        return cls(
            section=str(d.get("section", "")),
            username=str(d.get("username", "")),
            password=str(d.get("password", "")),
            target_user=str(d.get("target_user", "")),
            dm_note=str(d.get("dm_note", "")),
            message=str(d.get("message", "")),
            send_mode=mode,
            send_count=int(d.get("send_count", 1) or 1),
            interval_mode=interval,
            send_interval=float(d.get("send_interval", 0) or 0),
            send_interval_min=float(d.get("send_interval_min", 0) or 0),
            send_interval_max=float(d.get("send_interval_max", 0) or 0),
        )

    def to_settings_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
            "target_user": self.target_user,
            "dm_note": self.dm_note,
            "message": self.message,
            "send_mode": self.send_mode,
            "send_count": self.send_count,
            "interval_mode": self.interval_mode,
            "send_interval": self.send_interval,
            "send_interval_min": self.send_interval_min,
            "send_interval_max": self.send_interval_max,
        }

    def validate_required(self) -> bool:
        return all([self.section, self.username, self.password,
                    self.target_user, self.message])
