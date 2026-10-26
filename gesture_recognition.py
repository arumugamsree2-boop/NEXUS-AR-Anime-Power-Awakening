import math

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

class GestureRecognizer:
    """Simple landmark-based gesture recognition; results can vary with camera angle."""
    def finger_is_up(self, points, tip, pip):
        # In a mirrored webcam image, finger tips are generally above their middle joints.
        return points[tip][1] < points[pip][1]

    def recognize_one(self, hand):
        p = hand["points"]
        if len(p) < 21:
            return "UNKNOWN"

        index_up = self.finger_is_up(p, 8, 6)
        middle_up = self.finger_is_up(p, 12, 10)
        ring_up = self.finger_is_up(p, 16, 14)
        pinky_up = self.finger_is_up(p, 20, 18)
        thumb_index = distance(p[4], p[8])
        palm_width = max(1, distance(p[5], p[17]))
        pinch = thumb_index < palm_width * 0.48

        if pinch:
            return "PINCH"
        if index_up and middle_up and ring_up and pinky_up:
            return "OPEN PALM"
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return "FIST"
        if index_up and middle_up and not ring_up and not pinky_up:
            return "V SIGN"
        return "HAND TRACKED"

    def recognize(self, hands):
        return [{"gesture": self.recognize_one(hand), "label": hand["label"]} for hand in hands]
