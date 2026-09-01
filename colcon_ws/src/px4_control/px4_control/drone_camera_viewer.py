import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time

class DroneCameraViewerFast(Node):
    def __init__(self):
        super().__init__('drone_camera_viewer_fast')
        self.get_logger().info('Initializing Fast Zero-Latency Drone POV Viewer...')
        self.bridge = CvBridge()

        # AUTOMATIC WORLD DETECTION ENGINE
        self.camera_topic = None
        self.get_logger().info('Scanning ROS 2 network graph to auto-detect active Gazebo world...')
        
        while self.camera_topic is None and rclpy.ok():
            topic_names_and_types = self.get_topic_names_and_types()
            for topic_name, _ in topic_names_and_types:
                if 'camera_link/sensor/IMX214/image' in topic_name:
                    self.camera_topic = topic_name
                    break
            if self.camera_topic is None:
                self.get_logger().warn('Awaiting Gazebo video stream topic... Make sure Terminal 5 bridge is running!')
                time.sleep(1.0)

        self.get_logger().info(f'SUCCESS! Locked onto active world camera topic: {self.camera_topic}')

        # Subscribe directly to the dynamically discovered topic
        self.image_sub = self.create_subscription(Image, self.camera_topic, self.image_callback, 10)

    def image_callback(self, msg):
        try:
            # Instantly decode the ROS Image packet into an OpenCV frame with zero overhead
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Render the raw video directly on the desktop
            cv2.imshow("Drone POV Live Feed (High-Speed)", frame)

            if cv2.waitKey(1) & 0xFF == 27: # ESC key to close cleanly
                rclpy.shutdown()
        except Exception as e:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = DroneCameraViewerFast()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
