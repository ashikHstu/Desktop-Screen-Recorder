import sys
import cv2
import numpy as np
import pyaudio
import threading
import pyautogui
import wave
import ffmpeg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QCheckBox, QLabel
from PyQt5.QtCore import Qt
from datetime import datetime
import os

# Global variables
is_recording = False
pause = False
screen_thread = None
camera_thread = None
audio_thread = None
system_audio_thread = None

# Output file paths
output_dir = "recordings"
os.makedirs(output_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
screen_output = os.path.join(output_dir, f"screen_{timestamp}.mp4")
camera_output = os.path.join(output_dir, f"camera_{timestamp}.mp4")
microphone_audio_output = os.path.join(output_dir, f"mic_audio_{timestamp}.wav")
system_audio_output = os.path.join(output_dir, f"sys_audio_{timestamp}.wav")
final_output = os.path.join(output_dir, f"final_{timestamp}.mp4")

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
        global screen_thread, camera_thread, audio_thread, system_audio_thread
        if self.screen_checkbox.isChecked():
            screen_thread = threading.Thread(target=self.record_screen)
            screen_thread.start()
        if self.camera_checkbox.isChecked():
            camera_thread = threading.Thread(target=self.record_camera)
            camera_thread.start()
        if self.microphone_checkbox.isChecked():
            audio_thread = threading.Thread(target=self.record_microphone_audio)
            audio_thread.start()
        if self.system_audio_checkbox.isChecked():
            system_audio_thread = threading.Thread(target=self.record_system_audio)
            system_audio_thread.start()

    def stop_recording(self):
        global is_recording
        is_recording = False
        if screen_thread:
            screen_thread.join()
        if camera_thread:
            camera_thread.join()
        if audio_thread:
            audio_thread.join()
        if system_audio_thread:
            system_audio_thread.join()
        self.merge_files()

    def record_screen(self):
        global is_recording, pause
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        screen_size = pyautogui.size()
        out = cv2.VideoWriter(screen_output, fourcc, 30.0, screen_size)
        
        while is_recording:
            if not pause:
                screen = pyautogui.screenshot()
                frame = np.array(screen)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)
        out.release()

    def record_camera(self):
        global is_recording, pause
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(camera_output, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))
        
        while is_recording:
            if not pause:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
        cap.release()
        out.release()

    def record_microphone_audio(self):
        global is_recording, pause
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        wf = wave.open(microphone_audio_output, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        
        while is_recording:
            if not pause:
                data = stream.read(1024)
                wf.writeframes(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()

    def record_system_audio(self):
        global is_recording, pause
        # Placeholder for system audio recording logic
        pass

    def merge_files(self):
        input_stream = ffmpeg.input(screen_output)
        audio_stream = ffmpeg.input(microphone_audio_output)
        system_audio_stream = ffmpeg.input(system_audio_output) if self.system_audio_checkbox.isChecked() else None
        if self.camera_checkbox.isChecked():
            camera_stream = ffmpeg.input(camera_output)
            merged_video = ffmpeg.filter([input_stream, camera_stream], "overlay", "10:10")
            merged_video = ffmpeg.output(merged_video, final_output, vcodec='libx264', acodec='aac')
        else:
            merged_audio = ffmpeg.concat(audio_stream, system_audio_stream, v=0, a=1) if system_audio_stream else audio_stream
            merged_video = ffmpeg.output(input_stream, final_output, acodec='aac', audio=merged_audio)
        ffmpeg.run(merged_video)
        print(f"Final recording saved as: {final_output}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = RecorderApp()
    recorder.show()
    sys.exit(app.exec_())
