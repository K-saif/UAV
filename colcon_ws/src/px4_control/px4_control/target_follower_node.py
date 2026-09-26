import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
import math
import time

class TargetFollowerNode(Node):
    def __init__(self):
        super().__init__('target_follower_node')
        self.get_logger().info('Initializing YOLO Target Follower Node with Search Pattern...')

        self.bridge = CvBridge()
        
        # Load lightweight YOLO model
        self.model = YOLO('yolo11n.pt')  
        self.target_class_id = 32  # COCO class ID (e.g., 32 = sports ball / 0 = person)

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # PX4 Communication
        self.offboard_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos)
        self.trajectory_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos)
        self.command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos)

        self.local_pos_sub = self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1', self.local_pos_cb, qos)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_cb, qos)
        
        # Gazebo Camera Stream Subscription
        self.image_sub = self.create_subscription(
            Image, 
            '/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image', 
            self.image_cb, 
            10
        )

        # State Variables
        self.current_x = 0.0; self.current_y = 0.0; self.current_z = 0.0
        self.target_x = 0.0; self.target_y = 0.0; self.target_z = -2.5
        self.target_yaw = 0.0
        
        self.home_set = False
        self.mission_step = 'TAKEOFF'
        self.nav_state = 0
        self.offboard_counter = 0

        # SEARCH PATTERN STATE VARIABLES
        self.last_seen_time = time.time()
        self.search_state = 'IDLE'  # Options: 'IDLE', 'WAITING', 'SEARCH_YAW', 'SEARCH_ALTITUDE'
        self.search_start_yaw = 0.0
        self.yaw_rotated_total = 0.0
        self.base_search_z = -2.5
        self.altitude_step_dir = -1.0  # -1.0 = Climb (higher z offset in NED), 1.0 = Descend

        # High-frequency flight timer loop (20 Hz)
        self.timer = self.create_timer(0.05, self.timer_cb)

    def local_pos_cb(self, msg):
        self.current_x = msg.x; self.current_y = msg.y; self.current_z = msg.z
        if not self.home_set:
            self.target_x = msg.x
            self.target_y = msg.y
            self.home_set = True

    def status_cb(self, msg):
        self.nav_state = msg.nav_state

    def image_cb(self, msg):
        if self.mission_step != 'FOLLOWING':
            return

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        h, w, _ = frame.shape
        img_center_x = w / 2.0
        img_center_y = h / 2.0

        # Run inference
        results = self.model(frame, verbose=False)
        target_found = False

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id == self.target_class_id:
                    # Bounding Box Coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    target_center_x = (x1 + x2) / 2.0
                    target_center_y = (y1 + y2) / 2.0
                    box_area = (x2 - x1) * (y2 - y1)

                    # Draw Bounding Box & Target Line
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    cv2.line(frame, (int(img_center_x), int(img_center_y)), (int(target_center_x), int(target_center_y)), (0, 0, 255), 2)

                    # Calculate Horizontal Offset (Yaw Correction)
                    error_x = (target_center_x - img_center_x) / img_center_x
                    yaw_gain = 0.05
                    self.target_yaw += error_x * yaw_gain  

                    # Distance Estimation based on Box Area (Forward/Backward)
                    desired_area = (w * h) * 0.08  
                    area_error = (desired_area - box_area) / desired_area
                    move_gain = 0.08

                    if abs(area_error) > 0.1:
                        step = move_gain * area_error
                        self.target_x += step * math.cos(self.target_yaw)
                        self.target_y += step * math.sin(self.target_yaw)

                    target_found = True
                    break

        # SEARCH & TRACKING STATE MACHINE
        now = time.time()
        status_text= 'SEARCHING...'
        text_color = (0, 0, 255)
        if target_found:
            self.last_seen_time = now
            self.search_state = 'TRACKING'
            status_text = "TARGET LOCKED & FOLLOWING"
            text_color = (0, 255, 0)
        else:
            time_since_lost = now - self.last_seen_time

            if time_since_lost < 2.0:
                self.search_state = 'WAITING'
                status_text = f"TARGET LOST! Waiting... ({2.0 - time_since_lost:.1f}s)"
                text_color = (0, 215, 255)
            
            elif self.search_state in ['TRACKING', 'WAITING']:
                # Initiate 360-degree rotation search
                self.search_state = 'SEARCH_YAW'
                self.search_start_yaw = self.target_yaw
                self.yaw_rotated_total = 0.0
                status_text = "SEARCHING: Rotating 360 Deg..."
                text_color = (0, 165, 255)

            elif self.search_state == 'SEARCH_YAW':
                # Incrementally rotate yaw
                yaw_step = 0.03
                self.target_yaw += yaw_step
                self.yaw_rotated_total += yaw_step

                # Normalize yaw between -PI and PI
                if self.target_yaw > math.pi: self.target_yaw -= 2 * math.pi
                if self.target_yaw < -math.pi: self.target_yaw += 2 * math.pi

                if self.yaw_rotated_total >= 2 * math.pi:
                    # Completed full 360 rotation without finding target -> Shift altitude
                    self.search_state = 'SEARCH_ALTITUDE'
                    self.base_search_z = self.target_z
                    status_text = "SEARCHING: Adjusting Altitude..."
                    text_color = (0, 0, 255)
                else:
                    status_text = f"SEARCHING 360: {(self.yaw_rotated_total / (2 * math.pi)) * 100:.0f}%"
                    text_color = (0, 165, 255)

            elif self.search_state == 'SEARCH_ALTITUDE':
                # Shift Z setpoint up (-Z in NED) or down (+Z in NED) to tilt camera FOV
                altitude_shift = 1.0 * self.altitude_step_dir
                self.target_z = self.base_search_z + altitude_shift

                # Reset rotation tracking to perform another 360 sweep at the new height
                self.search_state = 'SEARCH_YAW'
                self.yaw_rotated_total = 0.0
                
                # Flip direction for the next search iteration (climb <-> descend)
                self.altitude_step_dir *= -1.0
                status_text = f"SEARCHING: New Altitude ({abs(self.target_z):.1f}m)"
                text_color = (0, 0, 255)

        cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
        cv2.imshow("YOLO Tracking Stream", frame)
        cv2.waitKey(1)

    def timer_cb(self):
        self.publish_offboard_mode()
        if not self.home_set: return

        if self.offboard_counter < 60:
            self.publish_trajectory(self.current_x, self.current_y, self.current_z, 0.0)
            self.offboard_counter += 1
            return

        if self.mission_step == 'TAKEOFF':
            self.publish_trajectory(self.target_x, self.target_y, -2.5, 0.0)
            if self.nav_state != 14:
                self.send_cmd(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
                self.send_cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)

            if abs(self.current_z - (-2.5)) < 0.2:
                self.get_logger().info('Takeoff complete. Target Tracking Active!')
                self.mission_step = 'FOLLOWING'
                self.last_seen_time = time.time()

        elif self.mission_step == 'FOLLOWING':
            self.publish_trajectory(self.target_x, self.target_y, self.target_z, self.target_yaw)

    def publish_offboard_mode(self):
        msg = OffboardControlMode()
        msg.timestamp = 0
        msg.position = True
        self.offboard_pub.publish(msg)

    def send_cmd(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.timestamp = 0; msg.command = command
        msg.param1 = param1; msg.param2 = param2
        msg.target_system = 1; msg.target_component = 1; msg.from_external = True
        self.command_pub.publish(msg)

    def publish_trajectory(self, x, y, z, yaw):
        msg = TrajectorySetpoint()
        msg.timestamp = 0; msg.position = [x, y, z]; msg.yaw = yaw
        self.trajectory_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = TargetFollowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()

if __name__ == '__main__':
    main()