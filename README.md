# SMART-EYE
SMART EYE is an AI-powered human detection and alert system using a mobile IP camera and YOLO for real-time surveillance. It captures images, records video, and sends instant email alerts when human activity is detected through a simple Tkinter GUI.
# 🧠 SMART EYE – Intelligent Human Detection & Alert System

**SMART EYE** is an AI-powered real-time surveillance system that uses a **mobile IP camera** and **YOLO-based human detection** to enhance security.  
It automatically detects human activity, captures images, records video footage, and sends instant **email alerts** via a user-friendly **Tkinter GUI**.
## 🚀 Features

- 🎥 **Live Video Streaming** – Monitors surroundings in real time using a mobile camera IP stream.  
- 🧍 **Human Detection (YOLO)** – Detects human presence accurately using YOLO object detection.  
- 📸 **Automatic Screenshot Capture** – Takes and saves snapshots whenever a person is detected.  
- 📩 **Email Alert System** – Instantly sends email notifications with the captured image.  
- 💾 **Video & Image Storage** – Stores video footage and screenshots in a permanent directory.  
- 📴 **Smart Deactivation** – Automatically stops monitoring when no human activity is detected.  
- 🖥️ **Interactive GUI** – Built with Tkinter for simple control and live preview.
## 🧩 Technologies Used

- **Python** – Core programming language  
- **OpenCV** – For video processing and frame capturing  
- **YOLOv8** – Real-time human detection and object recognition  
- **Tkinter** – Graphical user interface for easy control  
- **SMTP (smtplib)** – Email alert automation  
- **Pillow (PIL)** – Image handling and saving screenshots
## ⚙️ Installation & Setup

1. **Clone the Repository**
   ```bash
  INSTALLED AND SETUP
  git clone https://github.com/your-username/SMART-EYE.git
   cd SMART-EYE
   INSTALL DEPENDENCIES
   pip install opencv-python ultralytics pillow
RUN APPLICATION
Connect Your Mobile Camera

Install the IP Webcam app (Android) or any similar app.

Start the camera stream and copy the IP address (e.g., http://192.168.x.x:8080/video).

Paste this IP link into the Tkinter GUI when prompted.
## 📸 How It Works

1. The system connects to a mobile camera stream through its IP address.  
2. YOLO continuously analyzes video frames to detect human presence.  
3. When a person is detected:
   - A **screenshot** is automatically captured.  
   - The **video footage** is saved to the permanent storage folder.  
   - An **email alert** with the image is sent to the registered address.  
4. When no human activity is detected for a while, monitoring **pauses automatically** to save system resources.
