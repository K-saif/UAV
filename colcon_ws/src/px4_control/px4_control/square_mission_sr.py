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

        # Subscribers
        self.local_pos_sub = self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1', self.local_position_callback, qos_profile)
        self.status_sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v4', self.status_callback, qos_profile)

        # Core State Variables
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_heading = 0.0
        self.nav_state = 0
        self.arming_state = 0
        
        # Mission Control States
        self.mission_step = 'PRIME_STREAM' # New initial step
        self.home_x = 0.0
        self.home_y = 0.0
        self.home_set = False
        self.offboard_setpoint_counter = 0 # Track pre-flight packets

        # Run control loop at 20Hz (Required by PX4 Offboard mode)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('Node ready. Waiting for telemetry data stream...')

    def local_position_callback(self, msg):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_z = msg.z
        self.current_heading = msg.heading
        if not self.home_set:
            self.home_x = msg.x
            self.home_y = msg.y
            self.home_set = True
            self.get_logger().info(f'Home position established: X={self.home_x:.2f}, Y={self.home_y:.2f}')

    def status_callback(self, msg):
        self.nav_state = msg.nav_state
        self.arming_state = msg.arming_state

    def publish_offboard_control_mode(self):
        msg = OffboardControlMode()
        msg.timestamp = 0
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        self.offboard_mode_pub.publish(msg)

    def send_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.timestamp = 0
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
        # Always stream offboard heartbeat settings to prevent failsafes
        self.publish_offboard_control_mode()

        if not self.home_set:
            return

        # NEW STEP: Prime PX4 stream buffers with 100 packets (2 seconds) before arming
        if self.mission_step == 'PRIME_STREAM':
            self.publish_trajectory_setpoint(self.current_x, self.current_y, self.current_z, self.current_heading)
            self.offboard_setpoint_counter += 1
            if self.offboard_setpoint_counter > 100:
                self.get_logger().info('Stream primed. Initiating Takeoff sequence...')
                self.mission_step = 'TAKEOFF'

        elif self.mission_step == 'TAKEOFF':
            self.publish_trajectory_setpoint(self.home_x, self.home_y, -2.5, 0.0)
            
            if self.nav_state != 14:
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
            
            if abs(self.current_z - (-2.5)) < 0.2:
                self.get_logger().info('Takeoff complete! Proceeding 2m forward.')
                self.mission_step = 'FORWARD_2M'

        elif self.mission_step == 'FORWARD_2M':
            self.publish_trajectory_setpoint(self.home_x + 2.0, self.home_y, -2.5, 0.0)
            if abs(self.current_x - (self.home_x + 2.0)) < 0.2:
                self.get_logger().info('Moved 2m forward. Holding position and rotating right...')
                self.mission_step = 'TURN_RIGHT'

        elif self.mission_step == 'TURN_RIGHT':
            self.publish_trajectory_setpoint(self.home_x + 2.0, self.home_y, -2.5, 1.57)
            if abs(self.current_heading - 1.57) < 0.1:
                self.get_logger().info('Turn complete. Advancing 2m sideways.')
                self.mission_step = 'SIDEWAYS_2M'

        elif self.mission_step == 'SIDEWAYS_2M':
            self.publish_trajectory_setpoint(self.home_x + 2.0, self.home_y + 2.0, -2.5, 1.57)
            if abs(self.current_y - (self.home_y + 2.0)) < 0.2:
                self.get_logger().info('Arrived at final waypoint. Deploying Land Sequence.')
                self.mission_step = 'LAND'

        elif self.mission_step == 'LAND':
            if self.nav_state == 14: 
                self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
            
            if self.arming_state == 1: # 1 = Disarmed
                self.get_logger().info('Drone has safely landed and disarmed. Node shutdown complete.')
                self.timer.destroy()

    def publish_trajectory_setpoint(self, x, y, z, yaw):
        msg = TrajectorySetpoint()
        msg.timestamp = 0
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
