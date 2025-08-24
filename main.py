import sys, os
import mediapipe as mp

# Ensure Mediapipe DLLs are available
mp_dir = os.path.dirname(mp.__file__)
os.add_dll_directory(mp_dir)

from PyQt6.QtWidgets import QApplication
from login import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
