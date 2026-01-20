# InstaSend.py
import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "modules"))

from PyQt5.QtWidgets import QApplication
from ui.main_window import DMWindow


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    window = DMWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
