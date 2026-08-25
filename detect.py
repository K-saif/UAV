import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --------------------------------------------------
# MediaPipe Hand Landmarker
# --------------------------------------------------

MODEL_PATH = "hand_landmarker.task"

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)

detector = vision.HandLandmarker.create_from_options(options)


# --------------------------------------------------
# Gesture detection
# --------------------------------------------------

def finger_up(hand, tip, pip):
    """
    Check whether a finger is extended.

    tip = fingertip landmark
    pip = PIP joint landmark
    """

    return hand[tip].y < hand[pip].y


def detect_gesture(hand):
    """
    Detect basic hand gestures.
    """

    index_up = finger_up(hand, 8, 6)
    middle_up = finger_up(hand, 12, 10)
    ring_up = finger_up(hand, 16, 14)
    pinky_up = finger_up(hand, 20, 18)

    # ✋ Open palm
    if index_up and middle_up and ring_up and pinky_up:
        return "HOLD"

    # ☝️ Index finger
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "FORWARD"

    # ✌️ Two fingers
    if index_up and middle_up and not ring_up and not pinky_up:
        return "UP"

    # 🤟 Three fingers
    if index_up and middle_up and ring_up and not pinky_up:
        return "DOWN"

    # ✊ Fist
    if not index_up and not middle_up and not ring_up and not pinky_up:
        return "EMERGENCY_STOP"

    return "UNKNOWN"


# --------------------------------------------------
# Webcam
# --------------------------------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")


# --------------------------------------------------
# Main loop
# --------------------------------------------------

timestamp_ms = 0
last_command = None

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Mirror webcam
    frame = cv2.flip(frame, 1)

    # OpenCV BGR -> RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # MediaPipe image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    timestamp_ms += 33

    # Run hand detection
    result = detector.detect_for_video(
        mp_image,
        timestamp_ms
    )

    command = "NO_HAND"

    # --------------------------------------------------
    # Hand detected
    # --------------------------------------------------

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]

        command = detect_gesture(hand)

        # Draw landmarks
        for landmark in hand:

            x = int(landmark.x * frame.shape[1])
            y = int(landmark.y * frame.shape[0])

            cv2.circle(
                frame,
                (x, y),
                4,
                (0, 255, 0),
                -1
            )

    # --------------------------------------------------
    # Print command only when changed
    # --------------------------------------------------

    if command != last_command:

        print(f"Command: {command}")

        last_command = command

    # --------------------------------------------------
    # Display command
    # --------------------------------------------------

    cv2.putText(
        frame,
        f"Command: {command}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow(
        "Drone Gesture Control",
        frame
    )

    # ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break


# --------------------------------------------------
# Cleanup
# --------------------------------------------------

cap.release()
cv2.destroyAllWindows()
detector.close()