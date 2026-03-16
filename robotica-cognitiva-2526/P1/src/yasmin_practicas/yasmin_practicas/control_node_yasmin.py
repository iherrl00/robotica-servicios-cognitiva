#!/usr/bin/env python3
"""
Nodo de control con YASMIN - Ejercicio 6
Gestiona navegación entre waypoints con FSM visualizable
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import yaml
import os
import random
from ament_index_python.packages import get_package_share_directory

import yasmin
from yasmin import State, Blackboard, StateMachine
from yasmin_ros import ActionState, ServiceState
from yasmin_ros import set_ros_loggers
from yasmin_ros.basic_outcomes import SUCCEED, ABORT, CANCEL
from yasmin_viewer import YasminViewerPub

from navegacion_avanzada_multiplesnodos.action import NavigateToWaypoint
from navegacion_avanzada_multiplesnodos.srv import GetUserDecision
from std_msgs.msg import Bool


class InitState(State):
    """Estado inicial: carga waypoints y pregunta modo"""
    
    def __init__(self, node):
        super().__init__(outcomes=["ready", "failed"])
        self.node = node
        
    def execute(self, blackboard: Blackboard) -> str:
        yasmin.YASMIN_LOG_INFO("=== INICIANDO SISTEMA ===")
        
        # Cargar waypoints
        try:
            wp_path = os.path.join(
                get_package_share_directory('navegacion_avanzada'),
                'config', 'waypoints.yaml'
            )
            with open(wp_path, 'r') as f:
                data = yaml.safe_load(f)
                waypoints = data.get('waypoints', [])
        except:
            # Waypoints de ejemplo
            waypoints = [
                {'name': 'Punto1', 'x': 1.0, 'y': 0.0, 'z': 0.0, 'w': 1.0},
                {'name': 'Punto2', 'x': 2.0, 'y': 1.0, 'z': 0.0, 'w': 1.0},
                {'name': 'Punto3', 'x': 0.0, 'y': 2.0, 'z': 0.0, 'w': 1.0},
            ]
        
        if not waypoints:
            yasmin.YASMIN_LOG_ERROR("No hay waypoints disponibles")
            return "failed"
        
        blackboard["waypoints"] = waypoints
        blackboard["current_idx"] = 0
        blackboard["interrupt_requested"] = False
        
        yasmin.YASMIN_LOG_INFO(f"{len(waypoints)} waypoints cargados")
        
        # Preguntar modo
        req = GetUserDecision.Request()
        req.prompt = "¿Modo secuencial (s), aleatorio (a), o manual (m)?"
        
        future = self.node.dialogue_client.call_async(req)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=30.0)
        
        if future.result():
            decision = future.result().decision.lower()
            
            if 'manual' in decision or decision == 'm':
                blackboard["mode"] = "manual"
                blackboard["waypoint_indices"] = []
            elif 'aleat' in decision or decision == 'a':
                blackboard["mode"] = "random"
                indices = list(range(len(waypoints)))
                random.shuffle(indices)
                blackboard["waypoint_indices"] = indices
            else:
                blackboard["mode"] = "sequential"
                blackboard["waypoint_indices"] = list(range(len(waypoints)))
            
            yasmin.YASMIN_LOG_INFO(f"Modo seleccionado: {blackboard['mode']}")
            return "ready"
        
        return "failed"


class PrepareNavigationState(State):
    """Prepara el siguiente objetivo de navegación"""
    
    def __init__(self, node):
        super().__init__(outcomes=["goal_ready", "no_more_waypoints", "cancelled"])
        self.node = node
        
    def execute(self, blackboard: Blackboard) -> str:
        mode = blackboard["mode"]
        waypoints = blackboard["waypoints"]
        current_idx = blackboard["current_idx"]
        
        if mode == "manual":
            # Preguntar qué waypoint
            waypoint_list = "Waypoints disponibles:\n"
            for i, wp in enumerate(waypoints):
                waypoint_list += f"  {i+1}) {wp['name']}\n"
            
            req = GetUserDecision.Request()
            req.prompt = f"{waypoint_list}¿A qué punto ir? (1-{len(waypoints)} o 'x')"
            
            future = self.node.dialogue_client.call_async(req)
            rclpy.spin_until_future_complete(self.node, future, timeout_sec=30.0)
            
            if future.result():
                decision = future.result().decision
                
                if 'x' in decision or 'cancel' in decision:
                    return "cancelled"
                
                # Parsear número
                import re
                numbers = re.findall(r'\d+', decision)
                if numbers:
                    selected = int(numbers[0]) - 1
                    if 0 <= selected < len(waypoints):
                        waypoint = waypoints[selected]
                        blackboard["current_waypoint"] = waypoint
                        blackboard["current_idx"] = selected
                        return "goal_ready"
            
            return "cancelled"
        
        else:
            # Modo secuencial/aleatorio
            indices = blackboard["waypoint_indices"]
            
            if current_idx >= len(indices):
                yasmin.YASMIN_LOG_INFO("¡TODOS LOS WAYPOINTS COMPLETADOS!")
                return "no_more_waypoints"
            
            wp_idx = indices[current_idx]
            waypoint = waypoints[wp_idx]
            
            blackboard["current_waypoint"] = waypoint
            yasmin.YASMIN_LOG_INFO(f"Preparando {current_idx + 1}/{len(indices)}: {waypoint['name']}")
            
            return "goal_ready"


class NavigateState(ActionState):
    """Estado que ejecuta la navegación usando ActionState"""
    
    def __init__(self, node):
        super().__init__(
            NavigateToWaypoint,
            'navigate_to_waypoint',
            self.create_goal,
            set(),
            self.result_handler,
            self.feedback_handler
        )
        self.node = node
        
    def create_goal(self, blackboard: Blackboard) -> NavigateToWaypoint.Goal:
        wp = blackboard["current_waypoint"]
        
        goal = NavigateToWaypoint.Goal()
        goal.waypoint_name = wp['name']
        goal.x = float(wp['x'])
        goal.y = float(wp['y'])
        goal.z = float(wp['z'])
        goal.w = float(wp['w'])
        
        yasmin.YASMIN_LOG_INFO(f"Navegando a: {goal.waypoint_name}")
        return goal
    
    def feedback_handler(self, blackboard: Blackboard, feedback: NavigateToWaypoint.Feedback):
        # Log periódico
        distance = feedback.distance_remaining
        if int(distance * 2) % 5 == 0:
            yasmin.YASMIN_LOG_INFO(f"Distancia restante: {distance:.2f}m")
    
    def result_handler(self, blackboard: Blackboard, result: NavigateToWaypoint.Result) -> str:
        if result.success:
            yasmin.YASMIN_LOG_INFO(f"¡ÉXITO! {result.message}")
            return SUCCEED
        else:
            yasmin.YASMIN_LOG_ERROR(f"FALLO: {result.message}")
            return ABORT


class AskUserDecisionState(State):
    """Pregunta al usuario qué hacer tras llegar"""
    
    def __init__(self, node):
        super().__init__(outcomes=["continue", "repeat", "cancel"])
        self.node = node
        
    def execute(self, blackboard: Blackboard) -> str:
        mode = blackboard["mode"]
        
        req = GetUserDecision.Request()
        if mode == "manual":
            req.prompt = "¿Ir a otro punto (c), repetir este (r), o cancelar (x)?"
        else:
            req.prompt = "¿Continuar (c), repetir (r), o cancelar (x)?"
        
        future = self.node.dialogue_client.call_async(req)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=60.0)
        
        if future.result():
            decision = future.result().decision.lower()
            
            if 'x' in decision or 'cancel' in decision:
                return "cancel"
            elif 'r' in decision or 'repetir' in decision:
                return "repeat"
            else:
                # Incrementar índice si no es modo manual
                if mode != "manual":
                    blackboard["current_idx"] += 1
                return "continue"
        
        return "cancel"


class AskRetryState(State):
    """Pregunta si reintentar tras fallo"""
    
    def __init__(self, node):
        super().__init__(outcomes=["retry", "cancel"])
        self.node = node
        
    def execute(self, blackboard: Blackboard) -> str:
        req = GetUserDecision.Request()
        req.prompt = "Fallo en navegación. ¿Reintentar? (s/n)"
        
        future = self.node.dialogue_client.call_async(req)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=30.0)
        
        if future.result():
            decision = future.result().decision.lower()
            if 's' in decision or 'si' in decision:
                return "retry"
        
        return "cancel"


class ControlNodeYasmin(Node):
    """Nodo principal con YASMIN"""
    
    def __init__(self):
        super().__init__('control_node_yasmin')
        
        # Cliente de diálogo
        self.dialogue_client = self.create_client(
            GetUserDecision,
            'get_user_decision'
        )
        
        self.get_logger().info("Control Node YASMIN iniciado")
        
    def run(self):
        # Esperar servicios
        self.get_logger().info("Esperando servicios...")
        if not self.dialogue_client.wait_for_service(timeout_sec=10.0):
            self.get_logger().error("Timeout esperando dialogue_node")
            return
        
        # Crear FSM
        sm = StateMachine(outcomes=["finished", "cancelled", "failed"])
        
        # Añadir estados
        sm.add_state("INIT", InitState(self), 
                     transitions={"ready": "PREPARE", "failed": "failed"})
        
        sm.add_state("PREPARE", PrepareNavigationState(self),
                     transitions={
                         "goal_ready": "NAVIGATE",
                         "no_more_waypoints": "finished",
                         "cancelled": "cancelled"
                     })
        
        sm.add_state("NAVIGATE", NavigateState(self),
                     transitions={
                         SUCCEED: "ASK_USER",
                         ABORT: "ASK_RETRY",
                         CANCEL: "cancelled"
                     })
        
        sm.add_state("ASK_USER", AskUserDecisionState(self),
                     transitions={
                         "continue": "PREPARE",
                         "repeat": "PREPARE",
                         "cancel": "cancelled"
                     })
        
        sm.add_state("ASK_RETRY", AskRetryState(self),
                     transitions={
                         "retry": "PREPARE",
                         "cancel": "cancelled"
                     })
        
        # Publicar para YASMIN Viewer
        YasminViewerPub(sm, "ROSER_NAVIGATION")
        
        # Ejecutar FSM
        blackboard = Blackboard()
        
        try:
            outcome = sm(blackboard)
            self.get_logger().info(f"FSM terminó con: {outcome}")
        except KeyboardInterrupt:
            self.get_logger().info("Interrumpido por usuario")


def main():
    rclpy.init()
    set_ros_loggers()
    
    node = ControlNodeYasmin()
    
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
