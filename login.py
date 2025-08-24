# login.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
import os, sys
import mediapipe as mp
mp_dir = os.path.dirname(mp.__file__)
os.add_dll_directory(mp_dir)

from dashboard import DashboardWindow
import requests

# ====== SET THIS TO YOUR RAILWAY BACKEND URL (no trailing slash) ======
API_BASE_URL = "https://web-production-f83f0.up.railway.app"
# ======================================================================

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blink Tracker Login")
        self.setGeometry(100, 100, 300, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Login / Register")
        self.login_button.clicked.connect(self.handle_login)

        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Error", "Email and password cannot be empty.")
            return

        try:
            # 1️⃣ Attempt login
            r = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )

            if r.status_code == 401:
                # 2️⃣ User not found or wrong password → try registration
                reg = requests.post(
                    f"{API_BASE_URL}/auth/register",
                    json={
                        "name": email.split("@")[0],  # use email prefix as name
                        "email": email,
                        "password": password,
                        "consent": True
                    },
                    timeout=10
                )
                if reg.status_code >= 400:
                    QMessageBox.critical(self, "Register Failed", reg.text)
                    return
                # 3️⃣ Login again after successful registration
                r = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10
                )

            elif r.status_code >= 400:
                QMessageBox.critical(self, "Login Failed", r.text)
                return

            token = r.json().get("access_token")
            if not token:
                QMessageBox.critical(self, "Login Failed", "No token received from server.")
                return

        except requests.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"Could not reach backend.\n{e}")
            return

        from local_queue import delete_all
        delete_all()
        # Open dashboard with JWT token
        self.dashboard = DashboardWindow(user_email=email, token=token)
        self.dashboard.show()
        self.close()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
