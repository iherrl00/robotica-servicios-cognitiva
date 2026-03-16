#!/usr/bin/env python3
"""
Nodo de navegacion con CONTROLADORES LOCALES
Cambia entre DWB, TEB y RPP según criterios dinámicos
"""

from navegacion_avanzada_multiplesnodos.action import NavigateToWaypoint
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rclpy.action import ActionServer, CancelResponse
import rclpy
from rclpy.node import Node

class NavigationNode(Node):
    def __init__(self):
        super().__init__('navigation_node')
        
        # Navigator de Nav2
        self.navigator = BasicNavigator()
        
        # Cliente para cambiar CONTROLADORES LOCALES
        self.controller_client = self.create_client(
            SetParameters, 
            '/controller_server/set_parameters'
        )
        
        # Estado del controlador local
        self.current_controller = 'DWB'  # Controlador por defecto
        self.stuck_counter = 0
        self.last_distance = None
        
        # Action Server
        self.action_server = ActionServer(
            self,
            NavigateToWaypoint,
            'navigate_to_waypoint',
            self.execute_navigation,
            cancel_callback=self.cancel_callback
        )
        
        self.get_logger().info('Navigation Node iniciado (CONTROLADORES LOCALES: DWB, TEB, RPP)')
    
    def cancel_callback(self, goal_handle):
        """Acepta peticiones de cancelacion"""
        self.get_logger().info('Recibida peticion de cancelacion')
        return CancelResponse.ACCEPT
    
    def change_controller(self, controller_name):
        """Cambia el controlador local (DWB, TEB, RPP)"""
        if controller_name == self.current_controller:
            return
        
        if not self.controller_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('Servicio controller no disponible')
            return
        
        req = SetParameters.Request()
        param = Parameter()
        param.name = 'FollowPath.plugin'  # Parámetro del controlador
        
        # Mapear nombre a plugin completo
        plugin_map = {
            'DWB': 'dwb_core::DWBLocalPlanner',
            'TEB': 'teb_local_planner::TebLocalPlannerROS',
            'RPP': 'nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController'
        }
        
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=plugin_map.get(controller_name, 'dwb_core::DWBLocalPlanner')
        )
        req.parameters = [param]
        
        future = self.controller_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        
        if future.result():
            self.current_controller = controller_name
            self.get_logger().info(f'Controlador cambiado a: {controller_name}')
    
    def detect_stuck(self, current_distance):
        """Detecta si el robot esta atascado"""
        if self.last_distance is None:
            self.last_distance = current_distance
            return False
        
        if abs(current_distance - self.last_distance) < 0.05:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        
        self.last_distance = current_distance
        
        if self.stuck_counter >= 10:
            self.get_logger().warn('Robot atascado detectado')
            return True
        
        return False
    
    def execute_navigation(self, goal_handle):
        """Ejecuta navegacion con cambio inteligente de controladores"""
        goal = goal_handle.request
        
        self.get_logger().info(f'Navegando a: {goal.waypoint_name}')
        
        # Crear pose objetivo
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = goal.x
        pose.pose.position.y = goal.y
        pose.pose.orientation.z = goal.z
        pose.pose.orientation.w = goal.w
        
        # Enviar a Nav2
        self.navigator.goToPose(pose)
        
        # Reset variables
        self.stuck_counter = 0
        self.last_distance = None
        
        # Feedback loop con cambio inteligente de controladores
        feedback = NavigateToWaypoint.Feedback()
        
        while not self.navigator.isTaskComplete():
            # Verificar cancelacion
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.navigator.cancelTask()
                self.get_logger().info('Navegacion cancelada')
                
                result = NavigateToWaypoint.Result()
                result.success = False
                result.message = 'Cancelado por usuario'
                return result
            
            # Obtener feedback
            nav_feedback = self.navigator.getFeedback()
            
            if nav_feedback:
                remaining = nav_feedback.distance_remaining
                feedback.distance_remaining = remaining
                goal_handle.publish_feedback(feedback)
                

                # CRITERIOS DE CAMBIO DE CONTROLADOR LOCAL
                # CRITERIO 1: Distancia larga > 2.0m -> DWB (rápido y suave)
                if remaining > 2.0:
                    if self.current_controller != 'DWB':
                        self.get_logger().info('Área abierta (>2m) -> DWB')
                        self.change_controller('DWB')
                
                # CRITERIO 2: Distancia media 0.5-2.0m -> TEB (dinámico con obstáculos)
                elif 0.5 < remaining <= 2.0:
                    if self.current_controller != 'TEB':
                        self.get_logger().info('Navegación dinámica (0.5-2m) -> TEB')
                        self.change_controller('TEB')
                
                # CRITERIO 3: Aproximación final < 0.5m -> RPP (preciso)
                elif remaining <= 0.5:
                    if self.current_controller != 'RPP':
                        self.get_logger().info('Aproximación final (<0.5m) -> RPP')
                        self.change_controller('RPP')
                
                # CRITERIO 4: Atascado -> Cambiar a TEB (mejor con obstáculos)
                if self.detect_stuck(remaining):
                    self.get_logger().warn('Robot atascado -> TEB')
                    self.change_controller('TEB')
                    self.stuck_counter = 0
                
                # Log cada 2 metros aproximadamente
                if int(remaining * 5) % 10 == 0:
                    self.get_logger().info(
                        f'Distancia: {remaining:.2f}m | Controlador: {self.current_controller}'
                    )
            
            rclpy.spin_once(self, timeout_sec=0.5)
        
        # Resultado final
        result = NavigateToWaypoint.Result()
        nav_result = self.navigator.getResult()
        
        if nav_result == TaskResult.SUCCEEDED:
            result.success = True
            result.message = 'Waypoint alcanzado exitosamente'
            goal_handle.succeed()
            self.get_logger().info(f'Exito: {goal.waypoint_name}')
        else:
            result.success = False
            result.message = 'Fallo al alcanzar waypoint'
            goal_handle.abort()
            self.get_logger().error(f'Fallo: {goal.waypoint_name}')
        
        return result

def main():
    rclpy.init()
    node = NavigationNode()
    
    # Esperar Nav2
    node.get_logger().info('Esperando Nav2...')
    node.navigator.waitUntilNav2Active()
    node.get_logger().info('Nav2 activo')
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
