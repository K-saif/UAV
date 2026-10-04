
### Build and Execute!
Now compile your package and execute your program:
```bash
cd ~/colcon_ws
colcon build --packages-select px4_control
source ~/.bashrc
```


When you want to run your vision control node with the simulator, use **six separate terminal windows**:

before anything run, 

```bash
source ~/.bashrc
```

**replace [baylands.sdf](/baylands.sdf) with /PX4-Autopilot/Tools/simulation/gz/worlds/baylands.sdf**

### 🖥️ Terminal 1: Launch Gazebo Simulation (GPU Accelerated)
```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth_baylands
```

### 🌐 Terminal 2: Start Communication Bridge
```
MicroXRCEAgent udp4 -p 8888
```


### 📷 Terminal 3: create a bridge for drone cam feed
```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge /world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/image@sensor_msgs/msg/Image[gz.msgs.Image /world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo /depth_camera@sensor_msgs/msg/Image[gz.msgs.Image


```
**only run when needed drone feed**
note: replace with `world/baylands` with your current like `world/walls` 


### 🧠 Terminal 4: Run the Flight Control Node
```bash
source /opt/ros/jazzy/setup.bash
source ~/colcon_ws/install/setup.bash
ros2 run px4_control target_follower
```
------------------------------


