# Blink Tracker Desktop (PyQt6)

A cross-platform desktop client for Blink Tracker, built with **PyQt6**, **OpenCV**, and **Mediapipe**.  
It allows users to log in or register, track eye blinks in real-time, and sync data with the backend hosted on Railway.

## 🚀 Features

-  **Login / Register** with backend (JWT authentication)  
-  **Real-time blink detection** using Mediapipe  
-  **Sync blink counts** to backend API  
-  **View blink statistics** on the React dashboard  
  
##  Installation

-  **Clone the repository**
  ```
  git clone https://github.com/pratiksha220/Blink_Tracker_Desktop.git
  cd Blink_Tracker_Desktop
```
-  **Install Dependencies**
 ```
  pip install -r requirements.txt
```
-  **Run app**
  ```
  python main.py
```
##  Requirements

-  Dependencies are listed in requirements.txt

##  Tech Stack

**Python 3** - Core programming language
**PyQt6** - Desktop GUI framework
**OpenCV (cv2)** - Capturing webcam frames & image processing
**MediaPipe** - Real-time blink / face landmark detection
**NumPy** - Efficient numerical operations
**Requests** - API calls to backend
**Psutil** - System resource monitoring (if used for stats/logging)
**SQLite3 (via local_queue.py)** - Local storage & offline sync

##  Backend and Dashboard
-  Hosted on Railway

