import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy, ReliabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus
import math # Needed for sin() and cos() rotation math
from std_msgs.msg import String

class GestureDroneFlightNode(Node):
    def __init__(self):
        super().__init__('gesture_drone_flight_node')
        self.get_logger().info('Initializing Coordinate-Corrected Flight Node...')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publishers
        self.offboard_mode_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile)

        # Subscribers
        self.local_pos_sub = self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1', self.local_position_callback, qos_profile)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_callback, qos_profile)
        self.gesture_sub = self.create_subscription(String, '/gesture_command', self.gesture_callback, 10)

        # Vector states
        self.current_x = 0.0; self.current_y = 0.0; self.current_z = 0.0; self.current_heading = 0.0
        self.target_x = 0.0; self.target_y = 0.0; self.target_z = -2.0; self.target_yaw = 0.0
        self.nav_state = 0; self.arming_state = 0
        
        self.mission_step = 'PRIME_STREAM'
        self.home_set = False
        self.offboard_setpoint_counter = 0
        self.current_gesture = "NO_HAND"

        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('Flight Node Ready.')

    def local_position_callback(self, msg):
        self.current_x = msg.x; self.current_y = msg.y; self.current_z = msg.z; self.current_heading = msg.heading
        if not self.home_set:
            self.target_x = msg.x
            self.target_y = msg.y
            self.home_set = True

    def status_callback(self, msg):
        self.nav_state = msg.nav_state
        self.arming_state = msg.arming_state

    def gesture_callback(self, msg):
        self.current_gesture = msg.data

    def timer_callback(self):
        self.publish_offboard_control_mode()
        if not self.home_set: return

        if self.mission_step == 'PRIME_STREAM':
            self.publish_trajectory_setpoint(self.current_x, self.current_y, self.current_z, self.current_heading)
            self.offboard_setpoint_counter += 1
            if self.offboard_setpoint_counter > 60:
                self.mission_step = 'TAKEOFF'

        elif self.mission_step == 'TAKEOFF':
            self.publish_trajectory_setpoint(self.target_x, self.target_y, -2.0, 0.0)
            if self.nav_state != 14:
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
            
            if abs(self.current_z - (-2.0)) < 0.2:
                self.get_logger().info('Takeoff complete. Heading-Relative Tracking Active!')
                self.mission_step = 'FLIGHT_ACTIVE'

        elif self.mission_step == 'FLIGHT_ACTIVE':
            # SPEED CONFIGURATION CONSTANTS
            MOVE_SPEED = 0.16  # Increased from 0.04 (m/step) -> ~2.4 m/s
            YAW_SPEED  = 0.04  # Increased from 0.04 (rad/step) -> ~1.6 rad/s
            CLIMB_SPEED = 0.08 # Increased from 0.03 (m/step) -> ~1.2 m/s

            # Rotational Angular modifications
            if self.current_gesture == 'TURN_LEFT':
                self.target_yaw -= YAW_SPEED  
            elif self.current_gesture == 'TURN_RIGHT':
                self.target_yaw += YAW_SPEED  

            # Relative Directional movement calculation 
            if self.current_gesture == 'FORWARD':
                self.target_x += MOVE_SPEED * math.cos(self.target_yaw)
                self.target_y += MOVE_SPEED * math.sin(self.target_yaw)
                
            elif self.current_gesture == 'UP':
                self.target_z -= CLIMB_SPEED  
            elif self.current_gesture == 'DOWN':
                self.target_z += CLIMB_SPEED
                
            elif self.current_gesture == 'EMERGENCY_STOP':
                self.get_logger().warn('Fist detected! Engaging Land Routine.')
                self.mission_step = 'LAND'

            # Keep Yaw bounds wrapped within a healthy -PI to +PI spectrum
            if self.target_yaw > math.pi: self.target_yaw -= 2 * math.pi
            if self.target_yaw < -math.pi: self.target_yaw += 2 * math.pi

            # Stream targets
            self.publish_trajectory_setpoint(self.target_x, self.target_y, self.target_z, self.target_yaw)

        elif self.mission_step == 'LAND':
            if self.nav_state == 14:
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
            if self.arming_state == 1:
                self.get_logger().info('Flight closed.')
                self.timer.destroy()

    def publish_offboard_control_mode(self):
        msg = OffboardControlMode()
        msg.timestamp = 0; msg.position = True
        self.offboard_mode_pub.publish(msg)

    def send_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.timestamp = 0; msg.command = command
        msg.param1 = param1; msg.param2 = param2
        msg.target_system = 1; msg.target_component = 1; msg.from_external = True
        self.vehicle_command_pub.publish(msg)

    def publish_trajectory_setpoint(self, x, y, z, yaw):
        msg = TrajectorySetpoint()
        msg.timestamp = 0; msg.position = [x, y, z]; msg.yaw = yaw
        self.trajectory_setpoint_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = GestureDroneFlightNode()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
