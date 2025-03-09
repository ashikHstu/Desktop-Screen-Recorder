import cv2
import numpy as np
import mss
import pyaudio
import wave
import threading
import subprocess
import time
import tkinter as tk
from datetime import datetime

# GUI Setup
root = tk.Tk()
root.title("Screen Recorder")
root.geometry("375x667")  # Set window size like a mobile screen

# GUI settings
camera_enabled = tk.BooleanVar(master=root, value=True)
screen_enabled = tk.BooleanVar(master=root, value=True)
mic_audio_enabled = tk.BooleanVar(master=root, value=True)
system_audio_enabled = tk.BooleanVar(master=root, value=True)
recording = False
frames = []

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Audio recording setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
p = pyaudio.PyAudio()

def start_recording():
    global recording, frames, mic_stream, system_stream, audio_thread, video_thread, output_filename
    recording = True
    frames = []
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"output_{current_time}.mp4"
    
    if mic_audio_enabled.get():
        mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    if system_audio_enabled.get():
        system_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    audio_thread = threading.Thread(target=record_audio)
    video_thread = threading.Thread(target=record_video)
    
    audio_thread.start()
    video_thread.start()

def record_audio():
    global frames
    while recording:
        mic_data = mic_stream.read(CHUNK) if mic_audio_enabled.get() else b''
        system_data = system_stream.read(CHUNK) if system_audio_enabled.get() else b''
        frames.append(mic_data + system_data)

def record_video():
    global recording
    sct = mss.mss()
    monitor = sct.monitors[1]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("temp_video.mp4", fourcc, 20.0, (monitor['width'], monitor['height']))
    
    while recording:
        start_time = time.time()
        frame = None
        if screen_enabled.get():
            screen_img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)
        
        if camera_enabled.get():
            ret, cam_frame = cap.read()
            if ret:
                cam_frame = cv2.resize(cam_frame, (320, 240))
                if screen_enabled.get():
                    h, w, _ = frame.shape
                    frame[h-240:h, w-320:w] = cam_frame
                else:
                    frame = cam_frame
        
        if frame is not None:
            out.write(frame)
        
        elapsed_time = time.time() - start_time
        time.sleep(max(1/20.0 - elapsed_time, 0))
    
    out.release()

def stop_recording():
    global recording
    recording = False
    time.sleep(1)
    
    wf = wave.open("temp_audio.wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    subprocess.call(["ffmpeg", "-y", "-i", "temp_video.mp4", "-i", "temp_audio.wav", "-c:v", "copy", "-c:a", "aac", output_filename])
    subprocess.call([r"C:\ffmpeg\bin\ffmpeg.exe", "-y", "-i", "temp_video.mp4", "-i", "temp_audio.wav", "-c:v", "copy", "-c:a", "aac", output_filename])

    cap.release()
    cv2.destroyAllWindows()
    print("Recording saved as", output_filename)

# Checkboxes for options
tk.Checkbutton(root, text="Enable Camera", variable=camera_enabled).pack()
tk.Checkbutton(root, text="Enable Screen", variable=screen_enabled).pack()
tk.Checkbutton(root, text="Enable Mic Audio", variable=mic_audio_enabled).pack()
tk.Checkbutton(root, text="Enable System Audio", variable=system_audio_enabled).pack()

# Start/Stop buttons
tk.Button(root, text="Start Recording", command=start_recording).pack()
tk.Button(root, text="Stop Recording", command=stop_recording).pack()

root.mainloop()
