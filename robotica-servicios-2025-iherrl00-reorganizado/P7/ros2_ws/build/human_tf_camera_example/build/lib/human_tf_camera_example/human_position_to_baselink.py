#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
import math
import time

class HumanToBaseLink(Node):
    def __init__(self):
        super().__init__('human_to_baselink')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(0.5, self.lookup_transform)

        # Esperar un poco antes de empezar (dar tiempo a los broadcasters)
        self.get_logger().info("Esperando TFs iniciales...")
        time.sleep(3.0)

    def lookup_transform(self):
        try:
            # Verificar si el TF existe
            if not self.tf_buffer.can_transform('base_link', 'human_in_camera', rclpy.time.Time(), timeout=rclpy.duration.Duration(seconds=0.5)):
                self.get_logger().warn("Esperando que aparezca 'human_in_camera' en el árbol TF...")
                return

            tf = self.tf_buffer.lookup_transform('base_link', 'human_in_camera', rclpy.time.Time())
            x = tf.transform.translation.x
            y = tf.transform.translation.y
            z = tf.transform.translation.z
            dist = math.sqrt(x**2 + y**2 + z**2)
            self.get_logger().info(
                f"Humano respecto al portátil (base_link): x={x:.2f}, y={y:.2f}, z={z:.2f}, distancia={dist:.2f} m")

        except Exception as e:
            self.get_logger().warn(f"No se pudo transformar: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = HumanToBaseLink()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
