import sys
import cv2
import numpy as np
import pyaudio
import threading
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QCheckBox, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer
import pyautogui
import ffmpeg
from threading import Lock

# Global variables
is_recording = False
pause = False
screen_thread = None
camera_thread = None
audio_thread = None
lock = Lock()

# GUI Class
class RecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Recorder")
        self.setGeometry(200, 200, 400, 300)

        self.layout = QVBoxLayout()

        self.screen_checkbox = QCheckBox("Record Screen")
        self.layout.addWidget(self.screen_checkbox)

        self.camera_checkbox = QCheckBox("Record Camera")
        self.layout.addWidget(self.camera_checkbox)

        self.microphone_checkbox = QCheckBox("Record Microphone Audio")
        self.layout.addWidget(self.microphone_checkbox)

        self.system_audio_checkbox = QCheckBox("Record System Audio")
        self.layout.addWidget(self.system_audio_checkbox)

        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        self.layout.addWidget(self.record_button)

        self.pause_button = QPushButton("Pause/Resume")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.layout.addWidget(self.pause_button)

        self.setLayout(self.layout)

    def toggle_recording(self):
        global is_recording
        is_recording = not is_recording
        if is_recording:
            self.record_button.setText("Stop Recording")
            self.start_recording()
        else:
            self.record_button.setText("Start Recording")
            self.stop_recording()

    def toggle_pause(self):
        global pause
        pause = not pause

    def start_recording(self):
        global screen_thread, camera_thread, audio_thread
        screen_thread = threading.Thread(target=self.record_screen)
        camera_thread = threading.Thread(target=self.record_camera)
        audio_thread = threading.Thread(target=self.record_audio)
        
        screen_thread.start()
        camera_thread.start()
        audio_thread.start()

    def stop_recording(self):
        global is_recording
        is_recording = False
        screen_thread.join()
        camera_thread.join()
        audio_thread.join()

    def record_screen(self):
        global is_recording, pause
        while is_recording:
            if not pause:
                screen = pyautogui.screenshot()
                frame = np.array(screen)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # Write the frame to a video file or buffer
                # Add your recording logic here

    def record_camera(self):
        global is_recording, pause
        # Capture webcam
        cap = cv2.VideoCapture(0)
        while is_recording:
            if not pause:
                ret, frame = cap.read()
                if ret:
                    # Display and process camera frame here
                    # Add overlay position and logic for movable camera
                    pass
        cap.release()

    def record_audio(self):
        global is_recording, pause
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        while is_recording:
            if not pause:
                data = stream.read(1024)
                # Add audio processing and merging logic here

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = RecorderApp()
    recorder.show()
    sys.exit(app.exec_())
