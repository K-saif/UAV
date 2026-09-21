import cv2
import mediapipe as mp
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import time  # <--- Added to keep track of time duration

class GestureNode(Node):
    def __init__(self):
        super().__init__("gesture_node")
        self.publisher = self.create_publisher(String, "/gesture_command", 10)
        self.get_logger().info("Gesture node initialized. Continuous stream ready.")

    def publish_gesture(self, command):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)

def finger_up(hand, tip, pip):
    return hand[tip].y < hand[pip].y

def detect_gesture(hand):
    index_up = finger_up(hand, 8, 6)
    middle_up = finger_up(hand, 12, 10)
    ring_up = finger_up(hand, 16, 14)
    pinky_up = finger_up(hand, 20, 18)

    # ✋ Open palm
    if index_up and middle_up and ring_up and pinky_up: return "HOLD"
    # ☝️ Index finger
    if index_up and not middle_up and not ring_up and not pinky_up: return "UP"
    # ✌️ Two fingers
    if index_up and middle_up and not ring_up and not pinky_up: return "FORWARD"
    # 🤟 Three fingers
    if index_up and middle_up and ring_up and not pinky_up: return "DOWN"
    # ✊ Fist
    if not index_up and not middle_up and not ring_up and not pinky_up: return "FIST"
    
    # 🤘 Rock On sign (Index + Pinky) -> TURN_LEFT
    if index_up and not middle_up and not ring_up and pinky_up: return "TURN_LEFT"
    # 🤙 Pinky only up -> TURN_RIGHT
    if not index_up and not middle_up and not ring_up and pinky_up: return "TURN_RIGHT"

    return "UNKNOWN"

def main(args=None):
    rclpy.init(args=args)
    node = GestureNode()

    model_path = "/home/saif/colcon_ws/src/px4_control/px4_control/hand_landmarker.task"

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    timestamp_ms = 0

    # ------------------ TIMER VARIABLES ------------------
    fist_start_time = None
    FIST_HOLD_DURATION = 1.2  # Time required in seconds
    # -----------------------------------------------------

    while rclpy.ok():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        timestamp_ms += 33
        result = detector.detect_for_video(mp_image, timestamp_ms)
        detected_gesture = "NO_HAND"

        if result.hand_landmarks:
            hand = result.hand_landmarks[0]
            detected_gesture = detect_gesture(hand)

            for landmark in hand:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

        # ------------------ FIST DURATION LOGIC ------------------
        if detected_gesture == "FIST":
            if fist_start_time is None:
                fist_start_time = time.time()  # Start counting time
            
            elapsed_time = time.time() - fist_start_time
            
            if elapsed_time >= FIST_HOLD_DURATION:
                command = "EMERGENCY_STOP"
            else:
                # Still holding the fist, but hasn't reached 2 seconds yet
                command = "HOLD"  
                cv2.putText(frame, f"Hold Fist to Land: {FIST_HOLD_DURATION - elapsed_time:.1f}s", 
                            (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        else:
            # Reset timer if gesture is not a fist or no hand detected
            fist_start_time = None
            command = detected_gesture
        # ---------------------------------------------------------

        node.publish_gesture(command)
        rclpy.spin_once(node, timeout_sec=0)

        # Display screen feedback
        color = (0, 0, 255) if command == "EMERGENCY_STOP" else (0, 0, 0)
        cv2.putText(frame, f"Command: {command}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("Drone Gesture Control", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()