#!/usr/bin/env python3
"""
Nodo de control MEJORADO v2 con:
- Sistema de interrupcion basado en topics (sin conflictos stdin)
- Manejo robusto de timeouts en service calls
- Maquina de estados
- Modo secuencial/aleatorio
- Cancelacion y replanificacion
"""

from navegacion_avanzada_multiplesnodos.action import NavigateToWaypoint
from navegacion_avanzada_multiplesnodos.srv import GetUserDecision
from std_msgs.msg import Bool
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from enum import Enum
import yaml
import os
import random
from ament_index_python.packages import get_package_share_directory

class State(Enum):
    """Estados de la maquina"""
    IDLE = 0
    NAVEGANDO = 1
    PAUSADO = 2
    LLEGADO = 3
    PREGUNTANDO = 4
    CANCELADO = 5

class ControlNode(Node):
    def __init__(self):
        super().__init__('control_node')
        
        # Estado actual
        self.state = State.IDLE
        self.waypoints = []
        self.waypoint_indices = []
        self.current_idx = 0
        self.goal_handle = None
        self.mode = 'sequential'
        self.interrupt_requested = False
        
        # Action Client para navegacion
        self.nav_client = ActionClient(
            self,
            NavigateToWaypoint,
            'navigate_to_waypoint'
        )
        
        # Service Client para dialogo
        self.dialogue_client = self.create_client(
            GetUserDecision,
            'get_user_decision'
        )
        
        # Suscriptor para interrupciones (desde dialogue_node)
        self.interrupt_sub = self.create_subscription(
            Bool,
            'interrupt_signal',
            self.interrupt_callback,
            10
        )
        
        # Timer para procesar interrupciones pendientes
        self.interrupt_check_timer = self.create_timer(0.3, self.process_interruption)
        
        self.get_logger().info('Control Node iniciado v2 (sistema de interrupcion robusto)')
        self.get_logger().info('Presiona "i" + ENTER en cualquier momento para interrumpir')
        
    def interrupt_callback(self, msg):
        """Callback cuando se recibe señal de interrupcion"""
        if msg.data and self.state == State.NAVEGANDO:
            self.get_logger().info('*** SEÑAL DE INTERRUPCION recibida ***')
            self.interrupt_requested = True
    
    def process_interruption(self):
        """Procesa interrupciones pendientes"""
        if not self.interrupt_requested:
            return
        
        if self.state != State.NAVEGANDO:
            self.interrupt_requested = False
            return
        
        self.interrupt_requested = False
        self.get_logger().info('Procesando interrupcion...')
        self.handle_interruption()
    
    def call_dialogue_service(self, prompt, timeout_sec=10.0):
        """Llama al servicio de dialogo con timeout y manejo de errores"""
        req = GetUserDecision.Request()
        req.prompt = prompt
        
        self.get_logger().info(f'Preguntando: "{prompt}"')
        
        try:
            # Llamada asincrona con timeout
            future = self.dialogue_client.call_async(req)
            
            # Esperar con timeout
            start_time = self.get_clock().now()
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.1)
                
                if future.done():
                    response = future.result()
                    return response.decision.lower()
                
                # Verificar timeout
                elapsed = (self.get_clock().now() - start_time).nanoseconds / 1e9
                if elapsed > timeout_sec:
                    self.get_logger().warn(f'Timeout esperando respuesta ({timeout_sec}s)')
                    return 'continue'  # Respuesta por defecto
            
            return 'continue'
            
        except Exception as e:
            self.get_logger().error(f'Error llamando servicio de dialogo: {e}')
            return 'continue'
    
    def handle_interruption(self):
        """Maneja la interrupcion del usuario"""
        self.get_logger().info('=== NAVEGACION INTERRUMPIDA ===')
        self.transition_to(State.PAUSADO)
        
        # Cancelar navegacion actual
        if self.goal_handle:
            self.get_logger().info('Cancelando navegacion actual...')
            try:
                cancel_future = self.goal_handle.cancel_goal_async()
                rclpy.spin_until_future_complete(self, cancel_future, timeout_sec=5.0)
                self.get_logger().info('Navegacion cancelada')
            except Exception as e:
                self.get_logger().error(f'Error cancelando navegacion: {e}')
        
        # Preguntar que hacer
        decision = self.call_dialogue_service(
            '¿Continuar al mismo punto (c), o cancelar todo (x)?',
            timeout_sec=20.0
        )
        
        self.get_logger().info(f'Decision tras interrupcion: "{decision}"')
        
        if 'x' in decision or 'cancel' in decision:
            self.get_logger().info('Cancelando navegacion completa')
            self.transition_to(State.CANCELADO)
        
        elif 's' in decision or 'siguiente' in decision or 'next' in decision or 'otro' in decision:
            # Ir al siguiente waypoint
            self.get_logger().info('Saltando al siguiente waypoint')
            self.current_idx += 1
            if self.current_idx < len(self.waypoint_indices):
                self.send_navigation_goal()
            else:
                self.get_logger().info('No hay mas waypoints')
                self.transition_to(State.IDLE)
        
        else:  # Continuar mismo punto (default)
            self.get_logger().info('Continuando al mismo waypoint')
            self.send_navigation_goal()
    
    def load_waypoints(self):
        """Carga waypoints desde YAML"""
        try:
            wp_path = os.path.join(
                get_package_share_directory('navegacion_avanzada'),
                'config', 'waypoints.yaml'
            )
            
            with open(wp_path, 'r') as f:
                data = yaml.safe_load(f)
                self.waypoints = data.get('waypoints', [])
                
            self.get_logger().info(f'{len(self.waypoints)} waypoints cargados')
        except Exception as e:
            self.get_logger().error(f'Error cargando waypoints: {e}')
            # Waypoints de ejemplo
            self.waypoints = [
                {'name': 'Punto1', 'x': 1.0, 'y': 0.0, 'z': 0.0, 'w': 1.0},
                {'name': 'Punto2', 'x': 2.0, 'y': 1.0, 'z': 0.0, 'w': 1.0},
                {'name': 'Punto3', 'x': 0.0, 'y': 2.0, 'z': 0.0, 'w': 1.0},
            ]
            self.get_logger().info(f'Usando {len(self.waypoints)} waypoints de ejemplo')
    
    def ask_navigation_mode(self):
        """Preguntar modo de navegacion"""
        decision = self.call_dialogue_service(
            '¿Modo secuencial (s) o aleatorio (a)?',
            timeout_sec=30.0
        )
        
        self.get_logger().info(f'Decision modo: "{decision}"')
        
        if 'aleat' in decision or decision == 'a':
            self.mode = 'random'
            self.waypoint_indices = list(range(len(self.waypoints)))
            random.shuffle(self.waypoint_indices)
            self.get_logger().info('Modo ALEATORIO seleccionado')
        else:
            self.mode = 'sequential'
            self.waypoint_indices = list(range(len(self.waypoints)))
            self.get_logger().info('Modo SECUENCIAL seleccionado')
    
    def transition_to(self, new_state):
        """Cambio de estado"""
        self.get_logger().info(f'Estado: {self.state.name} -> {new_state.name}')
        self.state = new_state
    
    def send_navigation_goal(self):
        """Envia siguiente objetivo de navegacion"""
        if self.current_idx >= len(self.waypoint_indices):
            self.get_logger().info('No hay mas waypoints')
            self.transition_to(State.IDLE)
            return
            
        wp_idx = self.waypoint_indices[self.current_idx]
        waypoint = self.waypoints[wp_idx]
        
        goal = NavigateToWaypoint.Goal()
        goal.waypoint_name = waypoint['name']
        goal.x = float(waypoint['x'])
        goal.y = float(waypoint['y'])
        goal.z = float(waypoint['z'])
        goal.w = float(waypoint['w'])
        
        self.get_logger().info(f'Objetivo {self.current_idx + 1}/{len(self.waypoint_indices)}: {goal.waypoint_name}')
        self.get_logger().info('>>> Presiona "i" + ENTER para interrumpir <<<')
        
        send_goal_future = self.nav_client.send_goal_async(
            goal,
            feedback_callback=self.navigation_feedback_callback
        )
        
        send_goal_future.add_done_callback(self.navigation_goal_response_callback)
    
    def navigation_feedback_callback(self, feedback_msg):
        """Callback de feedback durante navegacion"""
        feedback = feedback_msg.feedback
        # Log menos frecuente para no saturar
        if int(feedback.distance_remaining * 2) % 5 == 0:
            self.get_logger().info(f'Restante: {feedback.distance_remaining:.2f}m')
    
    def navigation_goal_response_callback(self, future):
        """Callback cuando se acepta el objetivo"""
        self.goal_handle = future.result()
        
        if not self.goal_handle.accepted:
            self.get_logger().error('Objetivo rechazado')
            return
        
        self.transition_to(State.NAVEGANDO)
        
        get_result_future = self.goal_handle.get_result_async()
        get_result_future.add_done_callback(self.navigation_result_callback)
    
    def navigation_result_callback(self, future):
        """Callback cuando termina la navegacion"""
        # Solo procesar si no fue pausado
        if self.state == State.PAUSADO:
            self.get_logger().info('Resultado ignorado (navegacion pausada)')
            return
        
        result = future.result().result
        
        if result.success:
            self.get_logger().info(f'¡EXITO! {result.message}')
            self.transition_to(State.LLEGADO)
            self.ask_user_decision()
        else:
            self.get_logger().error(f'FALLO: {result.message}')
            self.ask_retry()
    
    def ask_retry(self):
        """Preguntar si reintentar tras fallo"""
        decision = self.call_dialogue_service(
            'Fallo en navegacion. ¿Reintentar? (s/n)',
            timeout_sec=30.0
        )
        
        if 's' in decision or 'si' in decision:
            self.send_navigation_goal()
        else:
            self.get_logger().info('Navegacion cancelada tras fallo')
            self.transition_to(State.CANCELADO)
    
    def ask_user_decision(self):
        """Pregunta al usuario que hacer tras llegar"""
        self.transition_to(State.PREGUNTANDO)
        
        decision = self.call_dialogue_service(
            '¿Continuar (c), repetir (r), o cancelar (x)?',
            timeout_sec=60.0
        )
        
        self.get_logger().info(f'Decision: {decision}')
        
        if 'x' in decision or 'cancel' in decision:
            self.get_logger().info('Navegacion cancelada')
            self.transition_to(State.CANCELADO)
        
        elif 'r' in decision or 'repetir' in decision:
            self.get_logger().info('Repitiendo waypoint')
            self.send_navigation_goal()
        
        else:  # Continuar
            self.current_idx += 1
            
            if self.current_idx < len(self.waypoint_indices):
                self.send_navigation_goal()
            else:
                self.get_logger().info('¡TODOS LOS WAYPOINTS COMPLETADOS!')
                self.transition_to(State.IDLE)
    
    def run(self):
        """Bucle principal"""
        self.load_waypoints()
        
        if not self.waypoints:
            self.get_logger().error('No hay waypoints disponibles')
            return
        
        # Esperar servicios
        self.get_logger().info('Esperando servicios...')
        if not self.nav_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('Timeout esperando navigation_node')
            return
        if not self.dialogue_client.wait_for_service(timeout_sec=10.0):
            self.get_logger().error('Timeout esperando dialogue_node')
            return
        self.get_logger().info('Servicios listos')
        
        # Preguntar modo
        self.ask_navigation_mode()
        
        # Iniciar navegacion
        self.current_idx = 0
        self.send_navigation_goal()
        
        # Spin
        try:
            rclpy.spin(self)
        except KeyboardInterrupt:
            self.get_logger().info('Ctrl+C detectado, finalizando...')

def main():
    rclpy.init()
    node = ControlNode()
    
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
