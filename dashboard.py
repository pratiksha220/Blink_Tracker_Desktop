import sys,os
import mediapipe as mp
mp_dir = os.path.dirname(mp.__file__)
os.add_dll_directory(mp_dir)

import time
import cv2

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer
import psutil
import requests

from local_queue import enqueue
from sync_worker import SyncWorker

# ====== SET THIS TO YOUR RAILWAY BACKEND URL (no trailing slash) ======
API_BASE_URL = "https://web-production-f83f0.up.railway.app"
# ======================================================================

class DashboardWindow(QWidget):
    def __init__(self, user_email=None, token =None):
        super().__init__()
        self.user_email = user_email
        self.token = token
        self.setWindowTitle(f"Blink Tracker Dashboard - {user_email if user_email else ''}")
        self.setGeometry(100, 100, 800, 600)

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Video feed label
        self.video_label = QLabel()
        layout.addWidget(self.video_label)
        
        self.cpu_label = QLabel("CPU Usage: ")
        self.mem_label = QLabel("Memory Usage: ")
        self.energy_label = QLabel("Energy Impact: ")
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.mem_label)
        layout.addWidget(self.energy_label)

        self.sync_status = QLabel("Sync: Initializing…")
        layout.addWidget(self.sync_status)

        # Blink count label
        self.blink_label = QLabel("Blinks: 0")
        self.blink_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.blink_label)

        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Camera setup
        self.cap = cv2.VideoCapture(0)

        # Blink tracking variables
        self.blink_count = 0
        self.eye_closed_frames = 0
        self.EYE_AR_THRESH = 0.21
        self.EYE_AR_CONSEC_FRAMES = 2

        # Background sync worker (posts to /blink)
        self.sync_worker = SyncWorker(
            api_base_url=API_BASE_URL,
            status_callback=self._set_sync_status,
            token = self.token
        )   
        self.blink_ready = True 
        self.eyes_closed=False
        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)
        # Timer for fetching history every 10 seconds
        self.history_timer = QTimer()
        self.history_timer.timeout.connect(self.fetch_history)
        self.history_timer.start(10000)  # 10 sec
        
    def _set_sync_status(self, text: str):
        # Called by SyncWorker thread (Qt allows updating labels from main thread;
        # but simple setText is usually fine; if you see warnings, use signals)
        self.sync_status.setText(f"Sync: {text}")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                left_eye = [face_landmarks.landmark[i] for i in [33, 160, 158, 133, 153, 144]]
                right_eye = [face_landmarks.landmark[i] for i in [263, 387, 385, 362, 380, 373]]

                def eye_aspect_ratio(eye):
                    from math import dist
                    vertical1 = dist((eye[1].x, eye[1].y), (eye[5].x, eye[5].y))
                    vertical2 = dist((eye[2].x, eye[2].y), (eye[4].x, eye[4].y))
                    horizontal = dist((eye[0].x, eye[0].y), (eye[3].x, eye[3].y))
                    return (vertical1 + vertical2) / (2.0 * horizontal)

                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)
                ear = (left_ear + right_ear) / 2.0

                if ear < self.EYE_AR_THRESH:
                    self.eye_closed_frames += 1
                    self.eyes_closed = True
                    
                else:
                    if self.eyes_closed and self.eye_closed_frames >= self.EYE_AR_CONSEC_FRAMES and self.blink_ready:
                        self.blink_count += 1
                        self.blink_label.setText(f"Blinks: {self.blink_count}")
                        if self.user_email and self.token:
                            enqueue({
                                "email": self.user_email,
                                "blink_count": 1,
                                "ts": time.time(),
                                "headers": {"Authorization": f"Bearer {self.token}"}
                            })
                        self.blink_ready = False
                    if not self.eyes_closed:
                        # Eyes have been open for a while → allow next blink
                        self.blink_ready = True    
                   
                    self.eye_closed_frames = 0
                    self.eyes_closed = False
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().used / (1024 ** 2)
        self.cpu_label.setText(f"CPU Usage: {cpu:.1f}%")
        self.mem_label.setText(f"Memory Usage: {mem:.2f} MB")
        self.energy_label.setText("Energy Impact: Simulated")

        # Convert to QImage
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def fetch_history(self):
        if not self.token or not self.user_email:
            return
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            r = requests.get(f"{API_BASE_URL}/blinks", headers=headers, timeout=5)
            if r.ok:
                data = r.json()
                if data:
                    latest = data[-1]  # last entry
                    # Use blink_count instead of total_blinks
                    self.blink_label.setText(
                        f"Blinks today: {latest['blink_count']}"
                    )
                else:
                    self.blink_label.setText("No data yet")
            else:
                self.blink_label.setText("Error fetching history")
        except requests.RequestException as e:
            self.blink_label.setText(f"Sync error: {e}")




    def closeEvent(self, event):
        try:
            self.cap.release()
        finally:
            # stop background sync thread
            if hasattr(self, "sync_worker") and self.sync_worker:
                self.sync_worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DashboardWindow()
    win.show()
    sys.exit(app.exec())
