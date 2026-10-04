import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
import math
import time

class TargetFollowerNode(Node):
    def __init__(self):
        super().__init__('target_follower_node')
        self.get_logger().info('Initializing YOLO + Depth Target Follower Node...')

        self.bridge = CvBridge()
        
        # Load lightweight YOLO model
        self.model = YOLO('yolo11n.pt')  
        self.target_class_id = 0  # COCO class ID (32 = sports ball / 0 = person)

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # PX4 Publishers & Subscribers
        self.offboard_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos)
        self.trajectory_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos)
        self.command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos)

        self.local_pos_sub = self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1', self.local_pos_cb, qos)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_cb, qos)
        
        # Gazebo Camera Stream Subscriptions (RGB & Depth)
        self.image_sub = self.create_subscription(
            Image, 
            '/world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/image', 
            self.image_cb, 
            qos
        )

        self.depth_sub = self.create_subscription(
            Image,
            '/depth_camera',  # UPDATED TO MATCH REAL GAZEBO TOPIC
            self.depth_cb,
            qos
        )

        # State Variables
        self.current_x = 0.0; self.current_y = 0.0; self.current_z = 0.0
        self.target_x = 0.0; self.target_y = 0.0; self.target_z = -2.5
        self.target_yaw = 0.0
        
        self.home_set = False
        self.mission_step = 'TAKEOFF'
        self.nav_state = 0
        self.offboard_counter = 0
        self.latest_depth_frame = None

        # Search Pattern State Variables
        self.last_seen_time = time.time()
        self.search_state = 'IDLE'  # 'IDLE', 'WAITING', 'SEARCH_YAW', 'SEARCH_ALTITUDE'
        self.search_start_yaw = 0.0
        self.yaw_rotated_total = 0.0
        self.base_search_z = -2.5
        self.altitude_step_dir = -1.0  # -1.0 = Climb in NED frame, 1.0 = Descend

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

    def depth_cb(self, msg):
        # Store latest depth image (32FC1 float representation in meters)
        self.latest_depth_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

    def image_cb(self, msg):
        if self.mission_step != 'FOLLOWING':
            return

        depth_cx = None
        depth_cy = None
        depth_rgb_cx = None
        depth_rgb_cy = None

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        h, w, _ = frame.shape
        img_center_x = w / 2.0
        img_center_y = h / 2.0

        # Run YOLO inference
        results = self.model(frame, verbose=False,conf=0.6)
        target_found = False
        target_distance = None

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id == self.target_class_id:
                    # Bounding Box Coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    target_center_x = (x1 + x2) / 2.0
                    target_center_y = (y1 + y2) / 2.0

                    # Draw Visual Hints
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    cv2.line(frame, (int(img_center_x), int(img_center_y)), (int(target_center_x), int(target_center_y)), (0, 0, 255), 2)
                    cv2.putText(frame, f"Target: ({target_center_x:.1f}, {target_center_y:.1f}) | Center: ({img_center_x:.1f}, {img_center_y:.1f})", 
                                (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # 1. Yaw Control (Center target horizontally)
                    error_x = (target_center_x - img_center_x) / img_center_x
                    yaw_gain = 0.05
                    self.target_yaw += error_x * yaw_gain  

                    # 2. Depth Distance Control (Maintain 3.0 Meters)
                    if self.latest_depth_frame is None:
                        self.get_logger().info("Depth frame NOT received yet! Check topic name or QoS.")
                    else:
                        depth = self.latest_depth_frame
                        finite = depth[np.isfinite(depth)]
                        if len(finite) > 0:
                            self.get_logger().info(
                                f"RGB shape={frame.shape}, "
                                f"Depth shape={depth.shape}, "
                                f"dtype={depth.dtype}, "
                                f"min={finite.min():.2f}, "
                                f"max={finite.max():.2f}"
                            )
                        else:
                            self.get_logger().warning("Entire depth frame contains no finite values!")

                        dh, dw = self.latest_depth_frame.shape

                        # Cast to explicit integers for NumPy array indexing
                        depth_cx = int(max(0, min(target_center_x, dw - 1)))
                        depth_cy = int(max(0, min(target_center_y, dh - 1)))

                        depth_rgb_cx = int(max(0, min(img_center_x, dw - 1)))
                        depth_rgb_cy = int(max(0, min(img_center_y, dh - 1)))

                        # Sample 11x11 patch around integer pixel coordinates
                        depth_crop = self.latest_depth_frame[
                            max(0, depth_cy - 5):min(dh, depth_cy + 6),
                            max(0, depth_cx - 5):min(dw, depth_cx + 6)
                        ]
                        valid_depths = depth_crop[np.isfinite(depth_crop)]

                        if len(valid_depths) > 0:
                            # 20th percentile targets the front surface of the object smoothly
                            target_distance = float(np.percentile(valid_depths, 20))
                            
                            DESIRED_DISTANCE = 5.0
                            dist_error = target_distance - DESIRED_DISTANCE
                            
                            # Lock altitude strictly to 2.0 meters (PX4 NED frame: Z = -2.0)
                            self.target_z = -2.0

                            # Proportional control with slightly higher speed limits
                            if abs(dist_error) > 0.20:
                                move_gain = 0.04      # Increased gain for faster acceleration (was 0.04)
                                MAX_STEP = 0.1       # Increased max step size for higher top speed (was 0.05)
                                
                                # Clamp step between -MAX_STEP and MAX_STEP
                                step = np.clip(move_gain * dist_error, -MAX_STEP, MAX_STEP)
                                
                                # Update position setpoints along heading vector
                                self.target_x += step * math.cos(self.target_yaw)
                                self.target_y += step * math.sin(self.target_yaw)
                        else:
                            self.get_logger().info("Target center depth pixels are all NaN / Inf!")
                    target_found = True
                    break

        # Search & State Machine Handling
        now = time.time()
        status_text = 'SEARCHING...'
        text_color = (0, 0, 255)

        if self.search_state in ['SEARCHING', 'IDLE']:
            self.search_state = 'SEARCH_YAW'
            self.search_start_yaw = self.target_yaw
            self.yaw_rotated_total = 0.0
            status_text = "SEARCHING: Rotating 360 Deg..."
            text_color = (0, 165, 255)
        if target_found:
            self.last_seen_time = now
            self.search_state = 'TRACKING'
            dist_str = f"{target_distance:.2f}m" if target_distance else "N/A"
            status_text = f"LOCKED | Dist: {dist_str}"
            text_color = (0, 255, 0)
        else:
            time_since_lost = now - self.last_seen_time

            if time_since_lost < 2.0:
                self.search_state = 'WAITING'
                status_text = f"TARGET LOST! Waiting... ({2.0 - time_since_lost:.1f}s)"
                text_color = (0, 215, 255)
            
            elif self.search_state in ['TRACKING', 'WAITING']:
                self.search_state = 'SEARCH_YAW'
                self.search_start_yaw = self.target_yaw
                self.yaw_rotated_total = 0.0
                status_text = "SEARCHING: Rotating 360 Deg..."
                text_color = (0, 165, 255)

            elif self.search_state == 'SEARCH_YAW':
                yaw_step = 0.03
                self.target_yaw += yaw_step
                self.yaw_rotated_total += yaw_step

                if self.target_yaw > math.pi: self.target_yaw -= 2 * math.pi
                if self.target_yaw < -math.pi: self.target_yaw += 2 * math.pi

                if self.yaw_rotated_total >= 2 * math.pi:
                    self.search_state = 'SEARCH_ALTITUDE'
                    self.base_search_z = self.target_z
                    status_text = "SEARCHING: Adjusting Altitude..."
                    text_color = (0, 0, 255)
                else:
                    status_text = f"SEARCHING 360: {(self.yaw_rotated_total / (2 * math.pi)) * 100:.0f}%"
                    text_color = (0, 165, 255)

            elif self.search_state == 'SEARCH_ALTITUDE':
                altitude_shift = 1.0 * self.altitude_step_dir
                self.target_z = self.base_search_z + altitude_shift

                self.search_state = 'SEARCH_YAW'
                self.yaw_rotated_total = 0.0
                self.altitude_step_dir *= -1.0
                status_text = f"SEARCHING: New Altitude ({abs(self.target_z):.1f}m)"
                text_color = (0, 0, 255)

        # -----------------------------
        # Depth Visualization
        # -----------------------------
        depth = self.latest_depth_frame

        if depth is not None:
            depth_vis = depth.copy()
            valid = np.isfinite(depth_vis)

            if np.any(valid):
                min_depth = np.min(depth_vis[valid])
                max_depth = np.max(depth_vis[valid])

                depth_normalized = np.zeros_like(depth_vis, dtype=np.uint8)
                depth_normalized[valid] = np.clip(
                    (depth_vis[valid] - min_depth) / (max_depth - min_depth + 1e-6) * 255,
                    0, 255
                ).astype(np.uint8)

                depth_colormap = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)

                # Mark the depth pixel corresponding to YOLO target
                if depth_cx is not None and depth_cy is not None:
                    sampled_depth = depth[depth_cy, depth_cx]

                    if np.isfinite(sampled_depth):
                        depth_text = f"{sampled_depth:.2f} m"
                    else:
                        depth_text = "NaN / Inf"

                    cv2.putText(
                        depth_colormap, depth_text, (20, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                    )

                    cv2.circle(depth_colormap, (depth_cx, depth_cy), 8, (255, 255, 255), -1)

                    cv2.putText(
                        depth_colormap, f"Target: ({depth_cx}, {depth_cy})", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                    )
                
                # Mark the depth pixel corresponding to RGB image center
                if depth_rgb_cx is not None and depth_rgb_cy is not None:
                    cv2.circle(depth_colormap, (depth_rgb_cx, depth_rgb_cy), 8, (0, 255, 255), -1)
                    cv2.putText(
                        depth_colormap, f"Center: ({depth_rgb_cx}, {depth_rgb_cy})", (20, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                    )

                cv2.imshow("Depth Camera", depth_colormap)
                cv2.waitKey(1)

        cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
        cv2.imshow("YOLO Depth Tracking Stream", frame)
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