# 🚁 PX4 Vision-Based Follow Me Drone

An autonomous **vision-based follow-me system** for PX4-powered multirotors running in Gazebo Sim with ROS 2 (Jazzy) and Micro XRCE-DDS.

The system uses an onboard **OAK-D-Lite** RGB-D camera and **YOLO** for real-time person detection. It estimates the person's position and distance from synchronized RGB and Depth frames, allowing the drone to dynamically adjust its **position, heading, and distance** while following the person.

The drone maintains a **5-meter follow distance** and **2-meter flight altitude**, with an autonomous search behavior when the person is temporarily lost.

---

## 📐 System Architecture & Features

- **🎯 Real-time Person Detection:** Uses YOLO inference to detect people in the RGB camera stream.

- **📷 Synchronized RGB-D Perception:** Aligns RGB and Depth frames to obtain the target's distance directly from the detected bounding-box center.

- **📏 Distance Keeping:** Maintains a target following distance of **5.0 m** using proportional distance control and smooth velocity clamping (`max step = 0.1 m/frame`) to reduce overshoot.

- **↔️ Horizontal Following:** Adjusts the drone's movement according to the target's horizontal displacement from the camera center.

- **🧭 Dynamic Yaw Alignment:** Continuously updates the drone's heading based on the target's horizontal image error.

- **⬆️ Altitude Lock:** Maintains a flight altitude of approximately **2.0 m** (`Z = -2.0 m` in the PX4 NED frame).

- **🔎 Autonomous Search:** If the person is lost for more than **2.0 seconds**, the drone initiates a 360° yaw search followed by altitude adjustments to reacquire the target.

---

## 🎯 Person Detection & Follow Strategy

The follow-me system uses **YOLO (You Only Look Once)** to detect people in the incoming RGB camera stream.

### Target Selection

The detection pipeline is restricted to **Class `0` (`person`)** from the standard COCO dataset.

Non-person detections are ignored to prevent unintended objects from becoming the follow target.

When multiple people are detected, the **largest person bounding box** is selected as the primary target.

### Target Position & Distance

The center of the selected bounding box is calculated as:

```python
x1, y1, x2, y2 = map(int, box.xyxy[0])

cx = (x1 + x2) // 2
cy = (y1 + y2) // 2
```

The `(cx, cy)` coordinates are then mapped to the synchronized Depth frame to obtain the person's estimated distance from the drone.

```python
self.target_class_id = 0

for box in results[0].boxes:
    cls_id = int(box.cls[0])

    if cls_id == 0:  # Class 0 = person
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
```

This RGB → Depth association provides the distance measurement required for autonomous following.

---

## 🧠 Follow-Me Control Pipeline

```text
        OAK-D-Lite
            │
      ┌─────┴─────┐
      │           │
     RGB        Depth
      │           │
      ▼           │
     YOLO         │
      │           │
      ▼           │
 Person BBox ─────┘
      │
      ▼
 Target Center (u, v)
      │
      ▼
 Depth Sampling
      │
      ▼
 Target Distance
      │
      ├──────────────► Distance Control
      │
      ├──────────────► Position Control
      │
      └──────────────► Yaw Control
                           │
                           ▼
                    PX4 Offboard Control
                           │
                           ▼
                       🚁 Drone
```

---

## 🛠️ Pre-Flight Setup

### 1. Update Gazebo World SDF

Before running the simulation, insert your custom actor/world SDF configuration into the PX4 Gazebo worlds directory.

Replace your local `baylands.sdf` file with the modified version:

```text
/PX4-Autopilot/Tools/simulation/gz/worlds/baylands.sdf
```

---

## 🏗️ Build Package

Compile the `px4_control` ROS 2 package:

```bash
cd ~/colcon_ws
colcon build --packages-select px4_control
source ~/.bashrc
```

---

## 🚀 Execution Guide

Run the simulation stack using **4 separate terminal windows**.

Source the environment in each terminal:

```bash
source ~/.bashrc
```

### 🖥️ Terminal 1 — Gazebo Simulation

Start the PX4 SITL instance using the `x500_depth` model in the `baylands` world:

if you have added custom actors into your world by running python script then run
```bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$HOME/gz_models
```

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth_baylands
```

---

### 🌐 Terminal 2 — Micro XRCE-DDS Agent

Start the communication bridge between PX4 and ROS 2:

```bash
MicroXRCEAgent udp4 -p 8888
```

---

### 📷 Terminal 3 — ROS 2 / Gazebo Sensor Bridge

Bridge the RGB camera, camera information, and depth camera topics from Gazebo into ROS 2:

```bash
source /opt/ros/jazzy/setup.bash

ros2 run ros_gz_bridge parameter_bridge \
/world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/image@sensor_msgs/msg/Image[gz.msgs.Image \
/world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo \
/depth_camera@sensor_msgs/msg/Image[gz.msgs.Image
```

> **Note:** If using a different world, such as `walls`, replace `/world/baylands` with `/world/walls` in the topic paths.

---

### 🧠 Terminal 4 — Vision Flight Control

Launch the autonomous follow-me node:

```bash
source /opt/ros/jazzy/setup.bash
source ~/colcon_ws/install/setup.bash

ros2 run px4_control target_follower
```

---

## 🚁 Follow-Me Behavior

Once the system is running:

1. PX4 initializes the drone in Gazebo.
2. The OAK-D-Lite provides synchronized RGB and Depth data.
3. YOLO detects the person.
4. The largest detected person is selected as the follow target.
5. The target's image coordinates are mapped to the Depth frame.
6. The system estimates the person's distance and horizontal displacement.
7. PX4 receives continuous offboard position/velocity commands.
8. The drone maintains approximately:
   - **5.0 m** distance from the person
   - **2.0 m** altitude
   - Target-centered yaw alignment
9. If the person disappears for more than **2 seconds**, the drone enters its autonomous search behavior.

---

## 🧩 Technology Stack

| Component | Technology |
|---|---|
| Flight Controller | PX4 Autopilot |
| Simulation | Gazebo Sim |
| Middleware | ROS 2 Jazzy |
| PX4 ↔ ROS 2 | Micro XRCE-DDS |
| Object Detection | YOLO |
| Depth Camera | OAK-D-Lite |
| Computer Vision | OpenCV |
| Programming | Python |
| Flight Control | PX4 Offboard Mode |

---

## 🚀 Project Goal

The goal of this project is to demonstrate an end-to-end **vision-guided autonomous follow-me drone**, combining real-time object detection, RGB-D perception, target distance estimation, and PX4 offboard flight control inside a simulated environment.

The same perception and control architecture can be extended to real-world autonomous UAV applications using an RGB-D camera or stereo/depth sensing system.