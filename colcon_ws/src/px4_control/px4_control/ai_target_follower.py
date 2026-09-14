import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy, ReliabilityPolicy
from sensor_msgs.msg import Image
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleLocalPosition, VehicleCommand, VehicleStatus
import cv2
import numpy as np
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy, ReliabilityPolicy
from sensor_msgs.msg import Image
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus
from cv_bridge import CvBridge
import cv2
import numpy as np
import time
import math
class AIVelocityFollower(Node):
    def __init__(self):
        super().__init__('ai_velocity_follower')
        self.get_logger().info('Initializing Stable Velocity AI Follower Node...')
        self.bridge = CvBridge()

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # PX4 Publishers
        self.offboard_mode_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_callback, qos_profile)

        # Shared AI Control Buffers
        self.target_visible = False
        self.last_seen_time = 0.0
        self.vx = 0.0          # Forward velocity (m/s)
        self.vy = 0.0          # Sideways velocity (m/s)
        self.yaw_speed = 0.0   # Rotational velocity (rad/s)
        self.nav_state = 0
        self.mission_step = 'TAKEOFF'

        # Auto-detect camera topic path
        self.camera_topic = None
        while self.camera_topic is None and rclpy.ok():
            for topic_name, _ in self.get_topic_names_and_types():
                if 'camera_link/sensor/IMX214/image' in topic_name:
                    self.camera_topic = topic_name
                    break
            if self.camera_topic is None: time.sleep(0.5)

        self.image_sub = self.create_subscription(Image, self.camera_topic, self.image_callback, 10)
        self.timer = self.create_timer(0.05, self.timer_callback)

    def status_callback(self, msg):
        self.nav_state = msg.nav_state

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            h, w, _ = frame.shape
            screen_center_x = w // 2

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array(), np.array()) + cv2.inRange(hsv, np.array(), np.array())
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 100:
                    self.target_visible = True
                    self.last_seen_time = time.time()
                    
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        target_cx = int(M["m10"] / M["m00"])
                        x, y, box_w, box_h = cv2.boundingRect(largest_contour)
                        cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (0, 255, 0), 2)

                        # ---- CLEAN VELICAL CONTROLS ----
                        pixel_error_x = target_cx - screen_center_x
                        
                        # Set rotational speed proportional to error (Negative to turn toward it)
                        self.yaw_speed = -float(pixel_error_x) * 0.005
                        
                        # If the target box is small (far away), command a safe forward velocity
                        if box_w < 160:
                            self.vx = 0.6  # Cruise forward at 0.6 m/s smoothly
                        else:
                            self.vx = 0.0  # Stop moving forward when close enough
            
            if time.time() - self.last_seen_time > 1.5:
                self.target_visible = False

            cv2.imshow("Drone Autonomous AI Tracking Engine Feed", frame)
            cv2.waitKey(1)
        except Exception: pass

    def timer_callback(self):
        # 1. Continuous heartbeat
        msg = OffboardControlMode()
        msg.timestamp = 0
        msg.position = False  # TURN OFF POSITION LOCKING
        msg.velocity = True   # ACTIVATE THE VELOCITY CONTROL MODULE!
        self.offboard_mode_pub.publish(msg)

        if self.mission_step == 'TAKEOFF':
            # Simple take-off command loop
            if self.nav_state != 14:
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
            else:
                self.get_logger().info('Hover altitude achieved. Velocity AI active!')
                self.mission_step = 'AI_ACTIVE'

        elif self.mission_step == 'AI_ACTIVE':
            setpoint = TrajectorySetpoint()
            setpoint.timestamp = 0
            
            if self.target_visible:
                # Directly stream velocity values! PX4 handles all vector alignments automatically.
                setpoint.velocity = [self.vx, self.vy, 0.0]
                setpoint.yawspeed = self.yaw_speed
            else:
                # Search mode: Spin slowly in place (0.4 rad/s) looking for the box
                setpoint.velocity = [0.0, 0.0, 0.0]
                setpoint.yawspeed = 0.4
                
            self.trajectory_setpoint_pub.publish(setpoint)

    def send_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.timestamp = 0; msg.command = command
        msg.param1 = param1; msg.param2 = param2
        msg.target_system = 1; msg.target_component = 1; msg.from_external = True
        self.vehicle_command_pub.publish(msg)

def main(args=None):
    from cv_bridge import CvBridge
    import rclpy
    rclpy.init(args=args)
    node = AIVelocityFollower()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
