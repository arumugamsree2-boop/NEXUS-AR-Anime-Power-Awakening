import cv2
import time
from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from effects import EffectsEngine
from ui import draw_hud, draw_help

WINDOW_NAME = "NEXUS AR | Anime Power Awakening"

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam. Close other camera apps and try again.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

    tracker = HandTracker(max_hands=2)
    recognizer = GestureRecognizer()
    effects = EffectsEngine()
    mode = "BLUE ORB"
    show_help = True
    prev_time = time.time()
    fps = 0.0

    print("\nNEXUS AR is running!")
    print("Keys: 1 Blue Orb | 2 Red Burst | 3 Purple Merge | 4 Portal")
    print("H help | C clear particles | Q quit\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Could not read webcam frame.")
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (960, 540))
        results = tracker.process(frame)
        hands = tracker.get_hands(results, frame.shape)
        gestures = recognizer.recognize(hands)

        now = time.time()
        dt = max(0.001, now - prev_time)
        fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps else 1.0 / dt
        prev_time = now

        # Keyboard selection always works; gestures also activate effects.
        if gestures:
            primary = gestures[0]
            if primary["gesture"] == "OPEN PALM":
                mode = "BLUE ORB"
            elif primary["gesture"] == "FIST":
                mode = "RED BURST"
            elif primary["gesture"] == "PINCH":
                mode = "PORTAL"

        if len(hands) >= 2:
            mode = "PURPLE MERGE"

        frame = effects.render(frame, hands, mode, dt)
        draw_hud(frame, mode, gestures, fps, len(hands))
        if show_help:
            draw_help(frame)

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("q"), ord("Q"), 27):
            break
        elif key == ord("1"):
            mode = "BLUE ORB"
        elif key == ord("2"):
            mode = "RED BURST"
        elif key == ord("3"):
            mode = "PURPLE MERGE"
        elif key == ord("4"):
            mode = "PORTAL"
        elif key in (ord("h"), ord("H")):
            show_help = not show_help
        elif key in (ord("c"), ord("C")):
            effects.clear()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
