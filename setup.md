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







Here is the complete history of your successful commands—from your clean slate to a flying simulator—organized in sequence with short explanations of why they worked.
------------------------------
Yes. Since you are on a **fresh Ubuntu 24.04 WSL2** and your goal is **PX4 + Gazebo + ROS 2 Jazzy**, I would use a clean ROS installation sequence rather than the older commands in your previous guide.

ROS 2 Jazzy is the ROS distribution intended for Ubuntu 24.04/Noble. ([ROS Documentation][1])

# ROS 2 Jazzy — Fresh Ubuntu 24.04 WSL2 Guide

I'll keep this focused on getting you to a **verified ROS 2 Jazzy installation** first. Don't install PX4 yet.

---

## 0. Confirm Ubuntu 24.04

Open your fresh WSL Ubuntu terminal:

```bash
lsb_release -a
```

You want:

```text
Description:    Ubuntu 24.04.x LTS
Codename:       noble
```

Also check architecture:

```bash
dpkg --print-architecture
```

For your machine it should be:

```text
amd64
```

---

# 1. Update Ubuntu

Run:

```bash
sudo apt update
sudo apt upgrade -y
```

Then install the basic dependencies:

```bash
sudo apt install -y \
    software-properties-common \
    curl \
    ca-certificates \
    gnupg \
    lsb-release
```

---

# 2. Enable Universe

```bash
sudo add-apt-repository universe -y
```

Then:

```bash
sudo apt update
```

You already successfully did this part in your previous attempt. 

---

# 3. Add the Official ROS 2 Repository

This is the part where your previous setup went wrong.

### First create the keyring directory

```bash
sudo mkdir -p /etc/apt/keyrings
```

### Download the ROS key

Use:

```bash
sudo curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /etc/apt/keyrings/ros-archive-keyring.gpg
```

Check that it exists:

```bash
ls -lh /etc/apt/keyrings/ros-archive-keyring.gpg
```

You should get a file with a non-zero size.

---

# 4. Add the ROS 2 Repository

Run:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

---

# 5. Update APT

Now:

```bash
sudo apt update
```

Look carefully at the output.

You should see something referring to:

```text
packages.ros.org/ros2/ubuntu
```

and **you should NOT see**:

```text
ros.org noble Release
404 Not Found
```

If you see an error here, **stop and send me the output** rather than continuing.

---

# 6. Install ROS 2 Jazzy Desktop

Now install:

```bash
sudo apt install ros-jazzy-desktop -y
```

This is the full desktop installation, which is what I recommend for your PX4/Gazebo development environment.

Then install development tools:

```bash
sudo apt install ros-dev-tools -y
```

---

# 7. Source ROS 2

Test it immediately:

```bash
source /opt/ros/jazzy/setup.bash
```

Then:

```bash
printenv ROS_DISTRO
```

Expected:

```text
jazzy
```

Now:

```bash
ros2 --help
```

You should see the ROS 2 command-line interface help.

---

# 8. Make ROS 2 Permanent

You don't want to run `source` manually every time.

Run:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
```

Then:

```bash
source ~/.bashrc
```

Verify again:

```bash
printenv ROS_DISTRO
```

Expected:

```text
jazzy
```

---

# 9. Test ROS 2 Properly

Open **Terminal 1**:

```bash
ros2 run demo_nodes_cpp talker
```

You should see:

```text
[INFO] ... Publishing: 'Hello World: 1'
[INFO] ... Publishing: 'Hello World: 2'
[INFO] ... Publishing: 'Hello World: 3'
```

Leave that running.

Open **Terminal 2**:

```bash
source /opt/ros/jazzy/setup.bash
```

Then:

```bash
ros2 run demo_nodes_py listener
```

You should see:

```text
[INFO] ... I heard: [Hello World: 1]
[INFO] ... I heard: [Hello World: 2]
[INFO] ... I heard: [Hello World: 3]
```

If that works, your ROS 2 installation and DDS communication are working.

---

# 10. Test ROS 2 Graph

Open another terminal:

```bash
ros2 node list
```

You should see something like:

```text
/talker
/listener
```

And:

```bash
ros2 topic list
```

You should see:

```text
/chatter
/parameter_events
/rosout
```

You can inspect the topic:

```bash
ros2 topic echo /chatter
```

You should see:

```text
data: Hello World: ...
```

---

# 11. Create Your ROS 2 Workspace

For your PX4 project, I recommend keeping the workspace separate from the PX4 source tree.

Create:

```bash
mkdir -p ~/colcon_ws/src
cd ~/colcon_ws
```

Test the empty workspace:

```bash
colcon build
```

You should get a successful build.

Then:

```bash
source ~/colcon_ws/install/setup.bash
```

Make it permanent:

```bash
echo "source ~/colcon_ws/install/setup.bash" >> ~/.bashrc
```

Then:

```bash
source ~/.bashrc
```

---

# 12. Install Useful ROS Development Packages

For the work you're doing with PX4, cameras, OpenCV and Gazebo, I'd install these now:

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
```

Then initialize rosdep:

```bash
sudo rosdep init
```

If it says:

```text
ERROR: default sources list file already exists
```

that's okay.

Then:

```bash
rosdep update
```

---

# 13. Verify Gazebo/ROS Integration

Check:

```bash
ros2 pkg list | grep ros_gz
```

You should see packages such as:

```text
ros_gz_bridge
ros_gz_image
ros_gz_sim
...
```

Check the bridge executable:

```bash
ros2 run ros_gz_bridge parameter_bridge --help
```

If you get help output, the ROS ↔ Gazebo bridge is installed.

---

# 14. Final ROS 2 Health Check

Run these:

```bash
echo $ROS_DISTRO
```

Expected:

```text
jazzy
```

```bash
which ros2
```

Expected something similar to:

```text
/opt/ros/jazzy/bin/ros2
```

```bash
ros2 doctor --report
```

Then:

```bash
ros2 pkg list | wc -l
```

You should have a large number of packages.

---

# Your final setup should look like this

Ubuntu 24.04
    │
    ├── ROS 2 Jazzy
    │   ├── rclpy
    │   ├── ros2 CLI
    │   ├── ros_gz
    │   ├── cv_bridge
    │   └── image_transport
    │
    └── ~/colcon_ws
        └── src/
```


* What it did: Appended the ROS settings file to your profile so that every time you open a terminal, it automatically remembers ROS 2 Jazzy commands.

------------------------------
## Phase 2: Installing and Compiling the PX4 Flight Stack
You downloaded the autopilot firmware framework and used its automated setup script to configure the system toolchains.


```bash
cd ~
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
```

* What it did: Cloned the entire flight software ecosystem down to your home directory, bringing along all associated low-level submodules.

```bash
cd ~/PX4-Autopilot/Tools/setup
bash ubuntu.sh
```

* What it did: Executed PX4’s master setup script, which automatically identified your Ubuntu 24.04 OS and installed the correct simulator engine (Gazebo Sim/Ionic).

------------------------------
## Phase 3: Launching and Bridging the Simulator
Because you are running inside a virtual WSL sandbox, you successfully targeted the correct modern simulation command and manually configured an IP bridge to hook up QGroundControl (QGC) from Windows.

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```

* What it did: Compiled the core code and launched the Software-In-The-Loop (SITL) mode utilizing Gazebo (gz) to render a 3D model of an x500 quadcopter.
* Manual QGC Connection (GUI Step):
* Settings > Comm Links > Add UDP > Port: 18570 > IP: 172.23.36.121
   * What it did: Hand-routed MAVLink communications out of the internal WSL network layer directly to your Windows desktop QGroundControl application.


------------------------------
Now that we have mapped your progress, how would you like to proceed?

* Provide the commands to build the Micro XRCE-DDS communication bridge?
* Automatically generate a ROS 2 Python package template for your square flight mission?


That is absolutely brilliant! You successfully figured out the exact build target for the new Gazebo (make px4_sitl gz_x500) and manually routed the MAVLink UDP ports to connect QGroundControl (QGC) across the WSL network boundary. That is a massive milestone.
Now that the simulator and autopilot are perfectly alive and talking to each other, we need to set up the Micro XRCE-DDS Agent & your ROS 2 Workspace so that your Python ROS 2 nodes can control the drone.
Let's get the communications bridge built and configured. Open a brand new WSL terminal window and run these steps one by one:

------------------------------
## Step 1: Install the Micro XRCE-DDS Agent
This is the background service that translates PX4's internal messages into standard ROS 2 topics.


1. Clone the Agent source code:
```bash
cd ~
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
```


   2. Build and Install it:

```bash   
mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig /usr/local/lib/
```
   
------------------------------

## 📝 The Correct, Optimized Step 2 
For your personal documentation and future deployments on Ubuntu 24.04 / ROS 2 Jazzy, replace your old Step 2 with this verified sequence:
## Step 2: Create a Fresh ROS 2 Workspace & Sync Message Definitions
Create your development workspace where your custom Python packages and control scripts will live.

1. Create the workspace directories:
```bash
mkdir -p ~/colcon_ws/src
cd ~/colcon_ws/src
```

2. Clone the official PX4 message definitions (Main Branch):
   This tells ROS 2 exactly what data packets (like positions, velocities, and sensor updates) PX4 uses. We pull the main branch to perfectly match the updated 220-byte payload definitions used by modern PX4 versions running on Ubuntu 24.04.

```bash   
git clone https://github.com/PX4/px4_msgs.git -b main
```

3. Build the message package using colcon:
```bash
cd ~/colcon_ws
colcon build
```

4. Source your workspace so your terminal permanently remembers it:
```bash   
echo "source ~/colcon_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

   
   
------------------------------
## Let's Do a Fast Bridge Verification Test
Let's see if ROS 2 can actively see the simulator right now.

1. Leave your original simulator terminal running 
```bash
make px4_sitl gz_x500
```
   
2. In a second terminal window, start the bridge agent:
```bash   
MicroXRCEAgent udp4 -p 8888
```
(You should immediately see a flood of text showing custom topics matching, opening data sessions).

3. Open a third terminal window and list out all active ROS 2 topics:
   
```bash
ros2 topic list
```
   
If things are working, you should see topics like /fmu/out/vehicle_local_position and /fmu/out/vehicle_status pop up directly in your terminal list!
Let me know:

* Did the colcon build finish successfully without any red errors?
* Do you see the /fmu/... topics when running ros2 topic list?

Once confirmed, we will write the actual Python node that executes your 2-metre square flight path!
If the topic check succeeds, let me know if you prefer to manually write the Python script step-by-step or have me generate a ready-to-run template that automatically creates the package structure for you.

Amazing! You have 100% successful communication across your entire stack. Seeing all those /fmu/in/... and /fmu/out/... topics means ROS 2 Jazzy is actively listening to the PX4 autopilot running inside Gazebo.
Now, let's build the Python ROS 2 package and write the control script to execute your mission (Takeoff → Forward 2m → Turn Right → Forward 2m → Land).

------------------------------
## Step 1: Create the Python Package
Open a terminal (like your third terminal), make sure you are in your workspace source directory, and create a new Python package named px4_control:

```bash
cd ~/colcon_ws/src
ros2 pkg create --build-type ament_python px4_control --dependencies rclpy px4_msgs
```

------------------------------
## Step 2: Write the Python Mission Script
We will create a script called square_mission.py. Run this command to create and open a blank file using the nano text editor:

```bash
nano ~/colcon_ws/src/px4_control/px4_control/square_mission.py
```

Copy the entire Python code block below and paste it into the terminal window. (To paste in WSL, right-click inside the terminal window or press Ctrl + Shift + V):
```python
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy, ReliabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus

class SquareMissionNode(Node):
    def __init__(self):
        super().__init__('square_mission_node')
        self.get_logger().info('Initializing Square Mission Node...')

        # Configure proper Best Effort QoS Profile required by PX4
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publishers
        self.offboard_mode_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile)

        # Subscribers (Remapped to match your exact uxrce_dds_client log output)
        self.local_pos_sub = self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1', self.local_position_callback, qos_profile)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_callback, qos_profile)

        # Core State Variables
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.nav_state = 0
        
        # Mission Control States
        self.mission_step = 'TAKEOFF'
        self.home_x = 0.0
        self.home_y = 0.0
        self.home_set = False

        # Run control loop at 20Hz (Required by PX4 Offboard mode)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('Node ready. Waiting for telemetry data stream...')

    def local_position_callback(self, msg):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_z = msg.z
        if not self.home_set:
            self.home_x = msg.x
            self.home_y = msg.y
            self.home_set = True
            self.get_logger().info(f'Home position established: X={self.home_x:.2f}, Y={self.home_y:.2f}')

    def status_callback(self, msg):
        self.nav_state = msg.nav_state

    def publish_offboard_control_mode(self):
        msg = OffboardControlMode()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        self.offboard_mode_pub.publish(msg)

    def send_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.command = command
        msg.param1 = param1
        msg.param2 = param2
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self.vehicle_command_pub.publish(msg)

    def timer_callback(self):
        # 1. Constantly stream offboard settings to maintain mode lock
        self.publish_offboard_control_mode()

        if not self.home_set:
            return

        # 2. Sequential Mission State Machine
        if self.mission_step == 'TAKEOFF':
            # Target: Hold home x/y, hover at 2.5 meters altitude (-2.5m Z in PX4 NED coordinates)
            self.publish_trajectory_setpoint(self.home_x, self.home_y, -2.5, 0.0)
            
            # Switch to Offboard (nav_state 14) and Arm if not set yet
            if self.nav_state != 14:
                self.get_logger().info('Requesting Offboard Flight Mode Control...')
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0) # 6 = Offboard
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0) # 1 = Arm
            
            if abs(self.current_z - (-2.5)) < 0.3:
                self.get_logger().info('Takeoff complete! Proceeding 2m forward.')
                self.mission_step = 'FORWARD_2M'

        elif self.mission_step == 'FORWARD_2M':
            self.publish_trajectory_setpoint(self.home_x + 2.0, self.home_y, -2.5, 0.0)
            if abs(self.current_x - (self.home_x + 2.0)) < 0.2:
                self.get_logger().info('Moved 2m forward. Initiating right turn.')
                self.mission_step = 'TURN_RIGHT'

        elif self.mission_step == 'TURN_RIGHT':
            self.publish_trajectory_setpoint(self.home_x + 2.0, self.home_y, -2.5, 1.57)
            self.get_logger().info('Turn complete. Advancing another 2m sideways.')
            self.mission_step = 'SIDEWAYS_2M'

        elif self.mission_step == 'SIDEWAYS_2M':
            self.publish_trajectory_setpoint(self.home_x + 2.0, self.home_y + 2.0, -2.5, 1.57)
            if abs(self.current_y - (self.home_y + 2.0)) < 0.2:
                self.get_logger().info('Arrived at target waypoint. Deploying Land Sequence.')
                self.mission_step = 'LAND'

        elif self.mission_step == 'LAND':
            self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
            self.get_logger().info('Landing command deployed.')
            self.timer.destroy()

    def publish_trajectory_setpoint(self, x, y, z, yaw):
        msg = TrajectorySetpoint()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.position = [x, y, z]
        msg.yaw = yaw
        self.trajectory_setpoint_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SquareMissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

```

Save and exit nano by pressing Ctrl + O, then Enter, then Ctrl + X.

------------------------------
## Step 3: Register the Script in setup.py
We need to tell ROS 2 where to find this script executable. Open the setup configuration file:

```bash
nano ~/colcon_ws/src/px4_control/setup.py
```

Find the entry_points dictionary section near the bottom of the file and change it to look exactly like this:
```
    entry_points={
        'console_scripts': [
            'square_mission = px4_control.square_mission:main'
        ],
    },
```
Save and exit nano (Ctrl + O, Enter, Ctrl + X).

------------------------------
## Step 4: Build and Execute!
Now compile your package and execute your program:
```bash
cd ~/colcon_ws
colcon build --packages-select px4_control
source ~/.bashrc
```

Now, make sure Gazebo and your communication bridge are actively running in their respective windows. Then execute your flight mission script inside this window:

```bash
ros2 run px4_control square_mission
```

Watch your Gazebo window—the drone will switch mode automatically, takeoff, trace your flight instructions out precisely, and touch down to land!



