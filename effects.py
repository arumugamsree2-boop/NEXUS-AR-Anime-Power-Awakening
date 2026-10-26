import cv2
import math
import random
import numpy as np

BLUE = (255, 150, 30)
CYAN = (255, 240, 100)
RED = (30, 45, 255)
PURPLE = (230, 60, 255)
WHITE = (245, 250, 255)

class EffectsEngine:
    """Lightweight OpenCV VFX: glow, rings, trails, particles and shockwaves."""
    def __init__(self):
        self.particles = []
        self.trails = {}
        self.elapsed = 0.0
        self.burst_cooldown = 0.0
        self.last_mode = None

    def clear(self):
        self.particles.clear()
        self.trails.clear()

    def add_burst(self, center, color, count=55, speed=220):
        cx, cy = center
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = random.uniform(speed * 0.25, speed)
            self.particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * velocity,
                "vy": math.sin(angle) * velocity,
                "life": random.uniform(0.35, 0.95),
                "max_life": 0.95,
                "radius": random.randint(2, 5),
                "color": color
            })

    def glow_circle(self, frame, center, radius, color, thickness=2, glow=16):
        overlay = frame.copy()
        cv2.circle(overlay, center, max(2, radius), color, thickness, cv2.LINE_AA)
        blurred = cv2.GaussianBlur(overlay, (0, 0), glow)
        cv2.addWeighted(blurred, 0.60, frame, 0.75, 0, frame)
        cv2.circle(frame, center, max(2, radius), color, thickness, cv2.LINE_AA)

    def orb(self, frame, center, t, color, radius=42):
        x, y = center
        for i in range(4):
            rr = radius + i * 9
            angle = t * (1.5 + i * 0.35) * (1 if i % 2 == 0 else -1)
            pts = []
            for step in range(90):
                a = step * math.tau / 90 + angle
                wobble = 1.0 + 0.10 * math.sin(a * 5 + t * 3 + i)
                pts.append((int(x + math.cos(a) * rr * wobble),
                            int(y + math.sin(a) * rr * 0.72 * wobble)))
            cv2.polylines(frame, [np.array(pts, np.int32)], True, color, 1 + (i % 2), cv2.LINE_AA)
        self.glow_circle(frame, center, radius, color, 3, 18)
        self.glow_circle(frame, center, max(7, radius // 3), WHITE, 2, 10)
        for i in range(8):
            a = t * 2.0 + i * math.tau / 8
            px = int(x + math.cos(a) * (radius + 17))
            py = int(y + math.sin(a * 1.2) * (radius + 10))
            cv2.circle(frame, (px, py), 3, WHITE, -1, cv2.LINE_AA)

    def portal(self, frame, center, t):
        x, y = center
        for i in range(6):
            radius = 32 + i * 12
            axes = (radius, int(radius * 1.28))
            angle = int((t * 45 * (1 if i % 2 == 0 else -1)) % 360)
            cv2.ellipse(frame, center, axes, angle, 0, 330, PURPLE if i % 2 else CYAN, 2, cv2.LINE_AA)
        for i in range(18):
            a = t * 2 + i * math.tau / 18
            px = int(x + math.cos(a) * 82)
            py = int(y + math.sin(a) * 105)
            cv2.circle(frame, (px, py), random.randint(2, 4), PURPLE, -1, cv2.LINE_AA)

    def update_particles(self, frame, dt):
        alive = []
        for part in self.particles:
            part["x"] += part["vx"] * dt
            part["y"] += part["vy"] * dt
            part["vy"] += 90 * dt
            part["life"] -= dt
            if part["life"] > 0:
                fade = max(0.15, part["life"] / part["max_life"])
                r = max(1, int(part["radius"] * fade))
                cv2.circle(frame, (int(part["x"]), int(part["y"])), r, part["color"], -1, cv2.LINE_AA)
                alive.append(part)
        self.particles = alive[-450:]

    def render(self, frame, hands, mode, dt):
        self.elapsed += dt
        self.burst_cooldown = max(0.0, self.burst_cooldown - dt)
        h, w = frame.shape[:2]

        centers = []
        for idx, hand in enumerate(hands):
            pts = hand["points"]
            # Use palm center to make the power sit naturally around the hand.
            palm = (int((pts[0][0] + pts[5][0] + pts[9][0] + pts[13][0] + pts[17][0]) / 5),
                    int((pts[0][1] + pts[5][1] + pts[9][1] + pts[13][1] + pts[17][1]) / 5))
            centers.append(palm)
            self.trails.setdefault(idx, []).append(palm)
            self.trails[idx] = self.trails[idx][-12:]
            if len(self.trails[idx]) > 2:
                for j in range(1, len(self.trails[idx])):
                    fade = j / len(self.trails[idx])
                    thickness = max(1, int(5 * fade))
                    cv2.line(frame, self.trails[idx][j-1], self.trails[idx][j], BLUE if mode == "BLUE ORB" else PURPLE, thickness, cv2.LINE_AA)

        if mode == "BLUE ORB" and centers:
            self.orb(frame, centers[0], self.elapsed, BLUE, 38)
        elif mode == "RED BURST" and centers:
            if self.burst_cooldown <= 0:
                self.add_burst(centers[0], RED, 42, 240)
                self.burst_cooldown = 0.45
            x, y = centers[0]
            for i in range(3):
                radius = int((self.elapsed * 210 + i * 45) % 135)
                cv2.circle(frame, (x, y), radius, RED, 2, cv2.LINE_AA)
        elif mode == "PURPLE MERGE" and centers:
            if len(centers) >= 2:
                center = ((centers[0][0] + centers[1][0]) // 2,
                          (centers[0][1] + centers[1][1]) // 2)
                self.orb(frame, center, self.elapsed, PURPLE, 55)
                cv2.line(frame, centers[0], centers[1], PURPLE, 2, cv2.LINE_AA)
            else:
                self.orb(frame, centers[0], self.elapsed, PURPLE, 48)
        elif mode == "PORTAL" and centers:
            self.portal(frame, centers[0], self.elapsed)

        self.update_particles(frame, dt)
        # Tiny energy sparks around detected hands.
        for center in centers:
            for _ in range(2):
                x = center[0] + random.randint(-45, 45)
                y = center[1] + random.randint(-45, 45)
                cv2.circle(frame, (x, y), 1, CYAN, -1, cv2.LINE_AA)
        return frame
