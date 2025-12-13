# NAVI - Navigation Assistant for the Visually Impaired
---

## 📖 Abstract
**NAVI** is an intelligent walking cane designed to restore autonomy and safety for the visually impaired. While traditional white canes only detect ground-level obstacles, NAVI implements a multi-sensor fusion architecture to perceive the environment in real-time. It identifies head-level hazards, recognizes objects (people, vehicles, signs), and provides turn-by-turn navigation through intuitive haptic and audio feedback.

By leveraging Edge AI on a Raspberry Pi and real-time sensor processing on an ESP32, NAVI offers a high-tech, low-cost alternative to expensive guide dogs or smart glasses.

---

## 🚀 Motivation
* **Rising Visual Impairment Cases:** Globally, 43 million people live with blindness, and vision loss is predicted to increase by 55% by 2050.
* **Limitations of Current Tech:** Traditional commercial canes lack environmental context (e.g., distinguishing a wall from a person) and cannot detect mid-height obstacles like low tree branches, etc.
* **Cost Barrier:** Guide dogs can cost over $30,000, and existing smart solutions are often prohibitively expensive. NAVI is built using commodity hardware to keep the Bill of Materials (BOM) under $200.

---

## 📖 Website:
Live Demo Video: https://www.youtube.com/watch?v=i3LiQw6iYxM

---

## ✨ Key Features

* **Multi-Level Obstacle Detection:** Utilizes Ultrasonic sensors and LiDAR to detect ground-level hazards (curbs, potholes) and body-level obstacles.
* **AI Object Recognition:** Runs a fine-tuned **YOLO v11 Nano** model on the edge to identify specific objects and calculate distance.
* **Directional Haptic Feedback:** Vibration motors provide spatial feedback (left, right, front) to guide users around obstacles.
* **Voice Assistant ("Hey Navi"):** A natural language interface powered by **OpenAI Whisper** and **LLMs** (via POE API). Users can ask, *"Where am I?"* or *"Navigate to Times Square."*
* **GPS Navigation:** Integrated turn-by-turn guidance via audio cues using OSRM/Google Maps API.
* **Emergency & Fall Detection:** Automatically detects falls using IMU data and publishes location alerts to **AWS IoT Core**.

---

## 🛠️ System Architecture

NAVI uses a dual-processor architecture: an **ESP32** for low-latency sensor fusion and a **Raspberry Pi 5** for high-level AI processing.

### Hardware Components

| Component | Function |
| :--- | :--- |
| **Raspberry Pi 5** | Core Edge AI processor (YOLO), Voice Assistant, and GPS routing. |
| **ESP32 (Feather)** | Microcontroller for sensor data acquisition and haptic motor control. |
| **Arducam ToF Camera** | Depth camera for visual obstacle recognition. |
| **TF-Luna LiDAR** | Servo-assisted 180° scanner for long-range mapping (up to 8m). |
| **VL53L0X ToF** | Short-range measurement for pothole and step detection. |
| **MPU6050 IMU** | 6-DOF Accelerometer + Gyroscope for fall detection. |
| **GNSS Module** | Real-time GPS/GLONASS positioning. |
| **Bone Conduction** | Audio feedback that maintains user awareness of ambient sounds. |

### Software Stack

* **Edge AI:** Ultralytics YOLO v11 Nano (ONNX) for object detection (~10 FPS).
* **Voice Pipeline:** `Porcupine` (Wake Word) → `Whisper` (STT) → `POE API` (LLM) → `pyttsx3` (TTS).
* **Connectivity:** MQTT over AWS IoT Core for app communication and alerts.
* **Firmware:** MicroPython (ESP32) for sensor signal conditioning.
* **Frontend:** Web Dashboard hosted on AWS EC2.
---

## ⚡ Installation & Setup

### Prerequisites
* **Raspberry Pi 5** (Raspberry Pi OS 64-bit)
* **ESP32** (MicroPython firmware)
* **Python 3.10+**
* Security Certificates from AWS IoT Core 

### 1. Execute on Raspberry Pi 
```bash
git clone --recursive-submodule https://github.com/devangguptaa/navi.git
cd navi

conda create -n navi python=3.12 -y 
conda activate navi 

cd navi-rpi
pip install -r requirements.txt

python3 voice_assistant.py 

#in another terminal 
python3 obstacle_depth.py 

# in another terminal 
python3 GPS_Module/aws_gps_publisher.py
``` 

### 2. Execute on ESP32 

```bash 
git clone --recursive-submodule https://github.com/devangguptaa/navi.git
cd navi/NAVI_Stick-ESP-Code-stack

mpfshell -nc "open <PORT_NAME>; mput."
``` 

