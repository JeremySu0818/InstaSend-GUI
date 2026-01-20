# utils/system.py
import sys
import os


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
