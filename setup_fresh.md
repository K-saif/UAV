# Install Gazebo Harmonic

The official Gazebo instructions provide Harmonic binaries for Ubuntu 24.04. ([Gazebo][2])

Install prerequisites:

```bash
sudo apt update
sudo apt install curl lsb-release gnupg -y
```

Add the OSRF repository:

```bash
sudo curl https://packages.osrfoundation.org/gazebo.gpg \
  --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
```

Then:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
```

Update:

```bash
sudo apt update
```

Install Harmonic:

```bash
sudo apt install gz-harmonic -y
```

---

## Verify Gazebo

Run:

```bash
gz sim --version
```

You should get something indicating:

```text
Gazebo Sim, version 8.x.x
```

Harmonic corresponds to Gazebo Sim 8.

Also:

```bash
which gz
```

You should get a valid executable path.

---

## Test Gazebo independently

Before involving PX4, test Gazebo itself:

```bash
gz sim
```

If the Gazebo GUI opens, close it with:

```text
Ctrl+C
```


---

# Master Setup Guide: ROS 2 Jazzy + PX4 + MediaPipe (Ubuntu 24.04)

## Phase 1: Base System, ROS 2 Jazzy, & Global Python Environment

### 1. Update Ubuntu & Install Prerequisites

Open your terminal and prepare the base system:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common curl ca-certificates gnupg lsb-release
sudo add-apt-repository universe -y
sudo apt update

```

### 2. Add Official ROS 2 Repository & Install Jazzy Desktop

```bash
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /etc/apt/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools

```

Make ROS 2 permanent in your shell:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc

```

### 3. Install Global Python Libraries & Handle NumPy Compatibility

Modern Ubuntu 24.04 enforces PEP 668. To ensure MediaPipe, OpenCV, and ROS 2 work harmoniously without NumPy version conflicts (`numpy<2`), install them globally using the override flag:

```bash
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-pip \
    python3-opencv \
    ros-jazzy-cv-bridge \
    ros-jazzy-image-transport \
    ros-jazzy-vision-msgs \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-image

# Install MediaPipe and enforce NumPy 1.x compatibility globally
pip3 install mediapipe "numpy<2" --break-system-packages

```

Initialize `rosdep`:

```bash
sudo rosdep init || true
rosdep update

```

---

## Phase 2: PX4 Autopilot & Gazebo Simulator

### 1. Clone PX4-Autopilot Source Code

```bash
cd ~
git clone https://github.com/PX4/PX4-Autopilot.git --recursive

```

### 2. Run the Automated Toolchain Script

```bash
cd ~/PX4-Autopilot/Tools/setup
bash ubuntu.sh

```

*Note: This script configures your toolchain and installs Gazebo Sim (Ionic) automatically for Ubuntu 24.04.*

---

## Phase 3: Micro XRCE-DDS Agent & ROS 2 Workspace

### 1. Build and Install Micro XRCE-DDS Agent

The agent translates internal PX4 flight messages into standard ROS 2 topics.

```bash
cd ~
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig /usr/local/lib/

```

### 2. Set Up `colcon_ws` and PX4 Message Definitions

```bash
mkdir -p ~/colcon_ws/src
cd ~/colcon_ws/src
git clone https://github.com/PX4/px4_msgs.git -b main

cd ~/colcon_ws
colcon build

```

Persist your workspace overlay in your shell:

```bash
echo "source ~/colcon_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc

```

---

## Phase 4: copy python files

### Create the Python Package
before copy, make sure you are in your workspace source directory, and create a new Python package named px4_control:

```bash
cd ~/colcon_ws/src
ros2 pkg create --build-type ament_python px4_control --dependencies rclpy px4_msgs
```


now, copy [px4](/UAV/colcon_ws/src/px4_control/px4_control/) folder to your px4_control folder



---

## Phase 5: Verification & Running the Simulation

### Build and Execute!
Now compile your package and execute your program:
```bash
cd ~/colcon_ws
colcon build --packages-select px4_control
source ~/.bashrc
```


When you want to run your vision control node with the simulator, use **six separate terminal windows**:

## One-Time System Configuration (Run This First)
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


