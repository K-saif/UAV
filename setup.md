
### Terminal 1 — PX4 + Gazebo Wall World

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth_walls
```

Wait until:

```text
INFO [commander] Ready for takeoff!
```

This starts PX4 SITL with the **X500 depth-camera drone and wall world**.

---

### Terminal 2 — Micro XRCE-DDS Agent

```bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros_uxrce_dds_ws/install/local_setup.bash

MicroXRCEAgent udp4 -p 8888
```

This establishes the **PX4 ↔ ROS 2 communication bridge**.

---

### Terminal 3 — Depth Camera Bridge

```bash
source /opt/ros/jazzy/setup.bash

ros2 run ros_gz_bridge parameter_bridge \
/depth_camera@sensor_msgs/msg/Image[gz.msgs.Image
```

This bridges the **Gazebo depth-camera image → ROS 2**.

---

### Terminal 4 — Perception

```bash
source /opt/ros/jazzy/setup.bash
source ~/drone/ros2_ws/install/setup.bash

ros2 run drone_perception depth_processor
```

The perception node processes the depth image and produces readings such as:

```text
L=7.2m | C=4.1m | R=7.0m | PATH CLEAR
```

or:

```text
L=7.1m | C=2.3m | R=6.8m | AVOID LEFT
```

So the current perception system can determine **left, center, and right obstacle distances** and make a basic avoidance decision.

---

### Terminal 5 — Autonomous Controller

Started only after the previous four terminals are working:

```bash
source /opt/ros/jazzy/setup.bash
source ~/drone/ros2_ws/install/setup.bash

ros2 run drone_control offboard_control
```



