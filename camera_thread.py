from PyQt5.QtCore import QThread, pyqtSignal
import pyrealsense2 as rs
import cv2
import mediapipe as mp
import numpy as np
from utils import euclidean_distance_3d

class CameraThread(QThread):
    frame_updated = pyqtSignal(np.ndarray)
    measurements_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.running = True
        self.capture_flag = False

        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(config)
        self.align = rs.align(rs.stream.color)

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()

    def run(self):
        while self.running:
            frames = self.pipeline.wait_for_frames()
            aligned = self.align.process(frames)
            color_frame = aligned.get_color_frame()
            depth_frame = aligned.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            results = self.pose.process(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))

            if results.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    color_image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

                if self.capture_flag:
                    landmarks = results.pose_landmarks.landmark
                    intr = aligned.get_profile().as_video_stream_profile().get_intrinsics()
                    coords = []

                    for idx in [0, 11, 12, 13, 14, 15, 16, 23, 24, 31, 32]:  # Required landmark indices
                        lm = landmarks[idx]
                        x, y = int(lm.x * 640), int(lm.y * 480)
                        depth = depth_frame.get_distance(x, y)
                        point = rs.rs2_deproject_pixel_to_point(intr, [x, y], depth)
                        coords.append(point)

                    height = euclidean_distance_3d(coords[0], [(coords[9][i] + coords[10][i]) / 2 for i in range(3)])
                    chest = euclidean_distance_3d(coords[1], coords[2])
                    bicep = euclidean_distance_3d(coords[1], coords[3])
                    thigh_to_feet = (euclidean_distance_3d(coords[7], coords[9]) + euclidean_distance_3d(coords[8], coords[10])) / 2
                    max_reach = max(euclidean_distance_3d(coords[9], coords[5]), euclidean_distance_3d(coords[10], coords[6]))

                    measurements = [round(max_reach, 2), round(chest, 2), round(bicep, 2), round(thigh_to_feet, 2), round(height, 2)]
                    self.measurements_ready.emit(measurements)
                    self.capture_flag = False

            self.frame_updated.emit(color_image)

    def stop(self):
        self.running = False
        self.pipeline.stop()
        self.quit()

    def capture(self):
        self.capture_flag = True
