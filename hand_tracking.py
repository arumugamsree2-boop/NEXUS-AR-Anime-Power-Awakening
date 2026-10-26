import cv2
import mediapipe as mp

class HandTracker:
    """Uses MediaPipe Hands to locate hand landmarks in webcam frames."""
    def __init__(self, max_hands=2, detection_confidence=0.65, tracking_confidence=0.60):
        self.max_hands = max_hands
        self.mp_hands = mp.solutions.hands
        self.drawer = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=0,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

    def get_hands(self, results, shape):
        height, width = shape[:2]
        hands = []
        if not results.multi_hand_landmarks:
            return hands

        for index, landmark_set in enumerate(results.multi_hand_landmarks):
            points = []
            for lm in landmark_set.landmark:
                points.append((int(lm.x * width), int(lm.y * height)))
            handedness = "Hand"
            if results.multi_handedness and index < len(results.multi_handedness):
                handedness = results.multi_handedness[index].classification[0].label
            hands.append({"points": points, "label": handedness})
        return hands
