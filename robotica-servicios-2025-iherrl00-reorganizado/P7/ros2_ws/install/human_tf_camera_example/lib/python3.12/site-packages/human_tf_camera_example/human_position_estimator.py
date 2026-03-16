#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import TransformStamped
from cv_bridge import CvBridge
import cv2
from tf2_ros import TransformBroadcaster
import math
import os



class HumanPositionEstimator(Node):
    def __init__(self):
        super().__init__('human_position_estimator')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.br = TransformBroadcaster(self)

        # Intentar cargar el clasificador Haar de la instalación de OpenCV o del sistema
        haar_path = ""
        if hasattr(cv2, "data"):
            haar_path = cv2.data.haarcascades
        else:
            # Ruta alternativa si cv2.data no existe
            haar_path = "/usr/share/opencv4/haarcascades/"

        self.face_cascade = cv2.CascadeClassifier(
            os.path.join(haar_path, 'haarcascade_frontalface_default.xml'))

        self.focal_length = 600.0
        self.real_face_height = 0.20

        self.latest_distance = None
        self.timer = self.create_timer(1.0, self.publish_distance) # cada 1 s


    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        h, w = frame.shape[:2]
        cx_img, cy_img = w / 2, h / 2

        for (x, y, fw, fh) in faces:
            Z = (self.real_face_height * self.focal_length) / fh
            X = (x + fw/2 - cx_img) * Z / self.focal_length
            Y = (y + fh/2 - cy_img) * Z / self.focal_length

            distance_camera = math.sqrt(X**2 + Y**2 + Z**2)
            # self.get_logger().info(f"Distancia humano respecto a cámara: {distance_camera:.2f} m")
            self.latest_distance = distance_camera

            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = 'camera_frame'
            t.child_frame_id = 'human_in_camera'
            t.transform.translation.x = float(Z)
            t.transform.translation.y = float(-X)
            t.transform.translation.z = float(-Y)
            t.transform.rotation.w = 1.0

            self.br.sendTransform(t)
            cv2.rectangle(frame, (x, y), (x+fw, y+fh), (0, 255, 0), 2)
            cv2.putText(frame, f"Z={Z:.2f}m", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow('Camera', frame)
        cv2.waitKey(1)

    def publish_distance(self):
        if self.latest_distance is not None:
            self.get_logger().info(f"Distancia humano respecto a cámara: {self.latest_distance:.2f} m")

def main():
    rclpy.init()
    node = HumanPositionEstimator()
    rclpy.spin(node)
    node.destroy_node()
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
