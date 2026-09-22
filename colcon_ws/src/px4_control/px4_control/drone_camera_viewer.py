import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time
import os

class DroneCameraViewerFast(Node):
    def __init__(self):
        super().__init__('drone_camera_viewer_fast')
        self.get_logger().info('Initializing Fast Zero-Latency Drone POV Viewer...')
        self.bridge = CvBridge()

        self.window_name = "Drone POV Live Feed (High-Speed)"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 720)

        # RECORDING & DYNAMIC FPS TRACKING
        self.output_filename = "drone_flight_recording.mp4"
        self.video_writer = None
        self.last_frame_time = None
        self.calculated_fps = 15.0  # Safe initial fallback for Gazebo
        self.frame_count = 0

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
                self.get_logger().warn('Awaiting Gazebo video stream topic...')
                time.sleep(1.0)

        self.get_logger().info(f'SUCCESS! Locked onto active world camera topic: {self.camera_topic}')
        self.image_sub = self.create_subscription(Image, self.camera_topic, self.image_callback, 10)

    def image_callback(self, msg):
        try:
            current_time = time.time()
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Calculate actual incoming FPS during the first 10 frames
            if self.last_frame_time is not None and self.video_writer is None:
                dt = current_time - self.last_frame_time
                if dt > 0:
                    self.calculated_fps = 1.0 / dt

            self.last_frame_time = current_time
            self.frame_count += 1

            # Initialize VideoWriter after 5 frames to get an accurate FPS estimate
            if self.video_writer is None and self.frame_count > 5:
                height, width, _ = frame.shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                
                # Cap minimum FPS to avoid divide-by-zero or extreme values
                fps_to_use = max(5.0, min(self.calculated_fps, 60.0))
                
                self.video_writer = cv2.VideoWriter(
                    self.output_filename, 
                    fourcc, 
                    fps_to_use, 
                    (width, height)
                )
                self.get_logger().info(
                    f'Started recording to: {os.path.abspath(self.output_filename)} '
                    f'({width}x{height} @ {fps_to_use:.1f} FPS detected)'
                )

            # Write frame if writer is initialized
            if self.video_writer is not None:
                self.video_writer.write(frame)

            # OSD Indicators
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (50, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow(self.window_name, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                rclpy.shutdown()

        except Exception as e:
            self.get_logger().error(f"Failed to process image frame: {str(e)}")

    def destroy_node(self):
        if self.video_writer is not None:
            self.video_writer.release()
            self.get_logger().info(f'Video recording saved cleanly: {self.output_filename}')
        super().destroy_node()

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
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()