import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class DroneCameraViewer(Node):
    def __init__(self):
        super().__init__('drone_camera_viewer')
        self.get_logger().info('Initializing Drone Camera Viewer Node...')

        # Convert ROS 2 images into openCV matrices
        self.bridge = CvBridge()

        # Subscribe to the mapped Gazebo camera hardware topic
        self.subscription = self.create_subscription(
            Image,
            '/world/baylands/model/x500_depth_0/link/camera_link/sensor/IMX214/image',
            self.image_callback,
            10
        )

        self.get_logger().info('Subscription locked onto /camera topic. Awaiting video stream feed...')

    def image_callback(self, msg):
        try:
            # Translate the ROS image message to an OpenCV BGR format image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Display the frame in a graphical window
            cv2.imshow("Drone POV Live Feed", cv_image)

            # Listen for ESC key to close window cleanly
            if cv2.waitKey(1) & 0xFF == 27:
                self.get_logger().info('Closing window sequence initiated.')
                rclpy.shutdown()
        except Exception as e:
            self.get_logger().error(f'Error processing incoming frame: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = DroneCameraViewer()
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
