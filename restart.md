
------------------------------
## Phase 1: Hardware Camera Attachment (Windows PowerShell)
Open a Windows PowerShell (as Administrator) on your desktop and bind your laptop camera to your Linux instance:
```bash
# 1. Look for your webcam's BUS ID (e.g., 2-1)
usbipd list
# 2. Attach it directly to your Ubuntu environment, in my case ID is 2-1
usbipd attach --wsl --busid 2-1
```
(Keep this PowerShell window open in the background while flying).

------------------------------
## Phase 2: One-Time System Configuration (Run This First)
Open one WSL terminal and paste these two commands to permanently ensure your NVIDIA RTX 5050 handles the graphics rendering and your webcam permissions are unlocked:
```bash
source ~/.bashrc
# Grant full reading/writing permission to any attached video devices
sudo chmod 666 /dev/video*
```
------------------------------
## Phase 3: The 4 Active Terminal Commands
Now, run these commands in their respective terminal windows to start your flight sequence:
## 🖥️ Terminal 1: Launch Gazebo Simulation (GPU Accelerated)
```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```
Once the pxh> prompt appears, remember to paste your infinite battery overrides:
```bash
param set COM_LOW_BAT_ACT 0
param set COM_OBL_BAT_ACT 0
```
if it gives warnings or errors, ignore for now

## 🌐 Terminal 2: Start Communication Bridge
```
MicroXRCEAgent udp4 -p 8888
```
## 🧠 Terminal 3: Run the Flight Control Node
```bash
source /opt/ros/jazzy/setup.bash
source ~/colcon_ws/install/setup.bash
ros2 run px4_control square_mission
```
## 📷 Terminal 4: Launch MediaPipe Hand Tracking Camera
```bash
source /opt/ros/jazzy/setup.bash
source ~/colcon_ws/install/setup.bash
ros2 run px4_control gesture_camera
```
------------------------------

**only run when needed drone feed**
note: replace with `world/baylands` with your current like `world/walls` 

## 📷 Terminal 5: create a bridge for drone cam feed
```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge '/world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/image@sensor_msgs/msg/Image@gz.msgs.Image'
```
------------------------------

## 📷 Terminal 6: create window for drone cam feed
```bash
source ~/colcon_ws/install/setup.bash
ros2 run px4_control drone_camera_viewer
```
------------------------------


