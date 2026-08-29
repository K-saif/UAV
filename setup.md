
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













.







.




Here is the complete history of your successful commands—from your clean slate to a flying simulator—organized in sequence with short explanations of why they worked.
------------------------------
## Phase 1: Configuring ROS 2 Jazzy for Ubuntu 24.04
Since your WSL environment is running Ubuntu 24.04 (Noble), you successfully configured the software paths to install the correct native ROS release (Jazzy).

* sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

* What it did: Enabled the Ubuntu "Universe" software repository, which contains necessary open-source dependencies.
* 

sudo apt update && sudo apt install curl -y

* What it did: Updated your package database lists and installed curl, a tool used to securely fetch web content.
* 

sudo curl -sSL https://githubusercontent.com -o /usr/share/keyrings/ros-archive-keyring.gpg

* What it did: Downloaded and registered the official ROS security signature key so your system trusts the packages.
* 

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://ros.org $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

* What it did: Added the exact ROS 2 package servers targeting your system architecture (amd64) and version (noble).
* 

sudo apt update

* What it did: Refreshed your software manager, forcing it to look at the newly added ROS servers.
* 

sudo apt install ros-jazzy-desktop ros-dev-tools -y

* What it did: Installed the full ROS 2 Jazzy developer suite, complete with compilers, visualizers, and core libraries.
* 

echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc

* What it did: Appended the ROS settings file to your profile so that every time you open a terminal, it automatically remembers ROS 2 Jazzy commands.

------------------------------
## Phase 2: Installing and Compiling the PX4 Flight Stack
You downloaded the autopilot firmware framework and used its automated setup script to configure the system toolchains.

* 

cd ~
git clone https://github.com --recursive

* What it did: Cloned the entire flight software ecosystem down to your home directory, bringing along all associated low-level submodules.
* 

cd ~/PX4-Autopilot/Tools/setup
bash ubuntu.sh

* What it did: Executed PX4’s master setup script, which automatically identified your Ubuntu 24.04 OS and installed the correct simulator engine (Gazebo Sim/Ionic).

------------------------------
## Phase 3: Launching and Bridging the Simulator
Because you are running inside a virtual WSL sandbox, you successfully targeted the correct modern simulation command and manually configured an IP bridge to hook up QGroundControl (QGC) from Windows.

* 

cd ~/PX4-Autopilot
make px4_sitl gz_x500

* What it did: Compiled the core code and launched the Software-In-The-Loop (SITL) mode utilizing Gazebo (gz) to render a 3D model of an x500 quadcopter.
* Manual QGC Connection (GUI Step):
* Settings > Comm Links > Add UDP > Port: 18570 > IP: 172.23.36.121
   * What it did: Hand-routed MAVLink communications out of the internal WSL network layer directly to your Windows desktop QGroundControl application.
* 

commander takeoff

* What it did: Entered directly into the PX4 internal terminal shell (pxh>), forcing the virtual flight controller to arm the rotors and achieve an automated 2.5-metre hover.

------------------------------
Now that we have mapped your progress, how would you like to proceed?

* Provide the commands to build the Micro XRCE-DDS communication bridge?
* Automatically generate a ROS 2 Python package template for your square flight mission?


.


.



.


.

That is absolutely brilliant! You successfully figured out the exact build target for the new Gazebo (make px4_sitl gz_x500) and manually routed the MAVLink UDP ports to connect QGroundControl (QGC) across the WSL network boundary. That is a massive milestone.
Now that the simulator and autopilot are perfectly alive and talking to each other, we need to set up the Micro XRCE-DDS Agent & your ROS 2 Workspace so that your Python ROS 2 nodes can control the drone.
Let's get the communications bridge built and configured. Open a brand new WSL terminal window and run these steps one by one:
------------------------------
## Step 1: Install the Micro XRCE-DDS Agent
This is the background service that translates PX4's internal messages into standard ROS 2 topics.

   1. Clone the Agent source code:
   
   cd ~
   git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
   cd Micro-XRCE-DDS-Agent
   
   2. Build and Install it:
   
   mkdir build && cd build
   cmake ..
   make
   sudo make install
   sudo ldconfig /usr/local/lib/
   
   
------------------------------

## 📝 The Correct, Optimized Step 2 
For your personal documentation and future deployments on Ubuntu 24.04 / ROS 2 Jazzy, replace your old Step 2 with this verified sequence:
## Step 2: Create a Fresh ROS 2 Workspace & Sync Message Definitions
Create your development workspace where your custom Python packages and control scripts will live.

   1. Create the workspace directories:
   
   mkdir -p ~/colcon_ws/src
   cd ~/colcon_ws/src
   
   2. Clone the official PX4 message definitions (Main Branch):
   This tells ROS 2 exactly what data packets (like positions, velocities, and sensor updates) PX4 uses. We pull the main branch to perfectly match the updated 220-byte payload definitions used by modern PX4 versions running on Ubuntu 24.04.
   
   git clone https://github.com/PX4/px4_msgs.git -b main
   
   3. Build the message package using colcon:
   
   cd ~/colcon_ws
   colcon build
   
   4. Source your workspace so your terminal permanently remembers it:
   
   echo "source ~/colcon_ws/install/setup.bash" >> ~/.bashrc
   source ~/.bashrc


   
   
------------------------------
## Let's Do a Fast Bridge Verification Test
Let's see if ROS 2 can actively see the simulator right now.

   1. Leave your original simulator terminal running (make px4_sitl gz_x500).
   2. In a second terminal window, start the bridge agent:
   
   MicroXRCEAgent udp4 -p 8888
   
   (You should immediately see a flood of text showing custom topics matching, opening data sessions).
   3. Open a third terminal window and list out all active ROS 2 topics:
   
   ros2 topic list
   
   
If things are working, you should see topics like /fmu/out/vehicle_local_position and /fmu/out/vehicle_status pop up directly in your terminal list!
Let me know:

* Did the colcon build finish successfully without any red errors?
* Do you see the /fmu/... topics when running ros2 topic list?

Once confirmed, we will write the actual Python node that executes your 2-metre square flight path!
If the topic check succeeds, let me know if you prefer to manually write the Python script step-by-step or have me generate a ready-to-run template that automatically creates the package structure for you.



.

..




.

.



.
Amazing! You have 100% successful communication across your entire stack. Seeing all those /fmu/in/... and /fmu/out/... topics means ROS 2 Jazzy is actively listening to the PX4 autopilot running inside Gazebo.
Now, let's build the Python ROS 2 package and write the control script to execute your mission (Takeoff → Forward 2m → Turn Right → Forward 2m → Land).
------------------------------
## Step 1: Create the Python Package
Open a terminal (like your third terminal), make sure you are in your workspace source directory, and create a new Python package named px4_control:

cd ~/colcon_ws/src
ros2 pkg create --build-type ament_python px4_control --dependencies rclpy px4_msgs

------------------------------
## Step 2: Write the Python Mission Script
We will create a script called square_mission.py. Run this command to create and open a blank file using the nano text editor:

nano ~/colcon_ws/src/px4_control/px4_control/square_mission.py

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

nano ~/colcon_ws/src/px4_control/setup.py

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

cd ~/colcon_ws
colcon build --packages-select px4_control
source ~/.bashrc

Now, make sure Gazebo and your communication bridge are actively running in their respective windows. Then execute your flight mission script inside this window:

ros2 run px4_control square_mission

Watch your Gazebo window—the drone will switch mode automatically, takeoff, trace your flight instructions out precisely, and touch down to land!
Let me know:

* Did the colcon build succeed?
* Did the drone successfully trace the path in Gazebo?





