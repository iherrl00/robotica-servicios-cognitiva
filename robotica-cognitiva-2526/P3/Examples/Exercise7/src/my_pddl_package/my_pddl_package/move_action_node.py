#!/usr/bin/env python3
"""
Ejercicio 8 — PlanSys2 Action Executor para la acción 'move'
Implementa el nodo ROS 2 que ejecuta físicamente cada (move ?from ?to)
enviando el goal a Nav2 NavigateToPose.

Uso:
  ros2 run my_pddl_package move_action_node.py

Requiere:
  - PlanSys2 corriendo con domain_simple.pddl
  - Nav2 activo (o tiago_simulator)
  - waypoints.yaml con coordenadas del mapa
"""

import os
import yaml

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from plansys2_support_py.ActionExecutorClient import ActionExecutorClient

from nav2_msgs.action import NavigateToPose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped


# ── Rutas ──────────────────────────────────────────────────────────────────────
HOME = os.path.expanduser("~")
WAYPOINTS_FILE = (
    HOME
    + "/pddl_ws/PDDL-course-main/Examples/Exercise7/"
    + "src/my_pddl_package/waypoints/waypoints.yaml"
)


def load_waypoints(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


class MoveActionNode(ActionExecutorClient):
    """
    Nodo executor para la acción PDDL:
        (move ?from - location ?to - location)

    PlanSys2 llama a este nodo cuando el executor necesita
    ejecutar una acción 'move' del plan.
    """

    def __init__(self):
        # Nombre de la acción PDDL que implementa este nodo
        super().__init__("move", 0.5)

        self.waypoints = load_waypoints(WAYPOINTS_FILE)
        self.navigator = BasicNavigator()
        self.get_logger().info("MoveActionNode ready. Waypoints loaded.")

    def do_work(self):
        """
        Llamado periódicamente por ActionExecutorClient mientras la acción está activa.
        """
        # Obtener argumentos del plan: [?from, ?to]
        args = self.get_arguments()
        if len(args) < 2:
            self.get_logger().error("Expected 2 arguments: from, to")
            self.finish(False, 0.0, "Missing arguments")
            return

        from_wp = args[0]
        to_wp   = args[1]

        self.get_logger().info(f"Moving from '{from_wp}' to '{to_wp}'")

        if to_wp not in self.waypoints:
            self.get_logger().error(f"Waypoint '{to_wp}' not found in yaml")
            self.finish(False, 0.0, f"Unknown waypoint: {to_wp}")
            return

        wp = self.waypoints[to_wp]
        pos = wp.get("position", {})
        ori = wp.get("orientation", {})

        # Construir goal pose
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = wp.get("frame_id", "map")
        goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()
        goal_pose.pose.position.x    = float(pos.get("x", 0.0))
        goal_pose.pose.position.y    = float(pos.get("y", 0.0))
        goal_pose.pose.position.z    = float(pos.get("z", 0.0))
        goal_pose.pose.orientation.x = float(ori.get("x", 0.0))
        goal_pose.pose.orientation.y = float(ori.get("y", 0.0))
        goal_pose.pose.orientation.z = float(ori.get("z", 0.0))
        goal_pose.pose.orientation.w = float(ori.get("w", 1.0))

        self.get_logger().info(
            f"Sending Nav2 goal → {to_wp} "
            f"(x={goal_pose.pose.position.x:.2f}, y={goal_pose.pose.position.y:.2f})"
        )

        self.navigator.goToPose(goal_pose)

        # Esperar hasta que Nav2 complete la navegación
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                remaining = Duration.from_msg(
                    feedback.estimated_time_remaining
                ).nanoseconds / 1e9
                self.get_logger().info(
                    f"  ETA: {remaining:.1f}s"
                )
            # Timeout de seguridad
            if feedback and Duration.from_msg(
                feedback.navigation_time
            ) > Duration(seconds=120.0):
                self.navigator.cancelTask()
                self.finish(False, 0.0, "Navigation timeout")
                return

        result = self.navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info(f"Arrived at '{to_wp}' ✅")
            self.finish(True, 1.0, f"Moved to {to_wp}")
        elif result == TaskResult.CANCELED:
            self.get_logger().warn("Navigation canceled")
            self.finish(False, 0.0, "Canceled")
        else:
            self.get_logger().error("Navigation failed")
            self.finish(False, 0.0, "Failed")


def main(args=None):
    rclpy.init(args=args)
    node = MoveActionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
