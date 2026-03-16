#!/usr/bin/env python3
"""
Nodo de control con maquina de estados
Coordina navegacion y dialogo
"""

#!/usr/bin/env python3
"""
Nodo de control COMPLETO con:
- Maquina de estados
- Modo secuencial/aleatorio
- Interrupcion durante navegacion
- Cancelacion y replanificacion
"""

from navegacion_avanzada_multiplesnodos.action import NavigateToWaypoint
from navegacion_avanzada_multiplesnodos.srv import GetUserDecision
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from enum import Enum
import yaml
import os
import random
import threading
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
        self.interruption_check = False
        
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
        
        # Timer para verificar interrupcion (cada 0.5 segundos)
        self.interrupt_timer = self.create_timer(0.5, self.check_interruption)
        
        self.get_logger().info('Control Node iniciado (con interrupcion)')
        
    def check_interruption(self):
        """Verifica si el usuario quiere interrumpir"""
        # Solo revisar si esta navegando
        if self.state != State.NAVEGANDO:
            return
        
        if self.interruption_check:
            return  # Ya hay una revision en curso
        
        # Preguntar de forma no bloqueante
        self.interruption_check = True
        thread = threading.Thread(target=self.ask_interrupt_async)
        thread.daemon = True
        thread.start()
    
    def ask_interrupt_async(self):
        """Pregunta si interrumpir (en thread separado)"""
        try:
            print("\n--- Presiona ENTER para interrumpir navegacion ---")
            # Esperar input con timeout
            import select
            import sys
            
            # Esperar 2 segundos maximo
            ready, _, _ = select.select([sys.stdin], [], [], 2)
            
            if ready:
                sys.stdin.readline()  # Consumir el ENTER
                self.handle_interruption()
        except:
            pass
        finally:
            self.interruption_check = False
    
    def handle_interruption(self):
        """Maneja la interrupcion del usuario"""
        if self.state != State.NAVEGANDO:
            return
        
        self.get_logger().info('INTERRUPCION detectada')
        self.transition_to(State.PAUSADO)
        
        # Cancelar navegacion actual
        if self.goal_handle:
            self.get_logger().info('Cancelando navegacion...')
            cancel_future = self.goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, cancel_future)
        
        # Preguntar que hacer
        req = GetUserDecision.Request()
        req.prompt = 'Navegacion interrumpida. Continuar mismo punto, ir a otro, o cancelar? (c/o/x)'
        
        future = self.dialogue_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        response = future.result()
        decision = response.decision.lower()
        
        self.get_logger().info(f'Decision interrupcion: "{decision}"')
        
        if decision == 'cancel' or 'x' in decision:
            self.get_logger().info('Cancelando navegacion completa')
            self.transition_to(State.CANCELADO)
        
        elif decision == 'otro' or 'o' in decision:
            # Ir al siguiente waypoint
            self.get_logger().info('Saltando al siguiente waypoint')
            self.current_idx += 1
            if self.current_idx < len(self.waypoint_indices):
                self.send_navigation_goal()
            else:
                self.get_logger().info('No hay mas waypoints')
                self.transition_to(State.IDLE)
        
        else:  # Continuar mismo punto (default)
            self.get_logger().info('Continuando al mismo punto')
            self.send_navigation_goal()
    
    def load_waypoints(self):
        """Carga waypoints desde YAML"""
        wp_path = os.path.join(
            get_package_share_directory('navegacion_avanzada'),
            'config', 'waypoints.yaml'
        )
        
        with open(wp_path, 'r') as f:
            data = yaml.safe_load(f)
            self.waypoints = data.get('waypoints', [])
            
        self.get_logger().info(f'{len(self.waypoints)} waypoints cargados')
    
    def ask_navigation_mode(self):
        """Preguntar modo de navegacion"""
        req = GetUserDecision.Request()
        req.prompt = 'Modo secuencial o aleatorio? (s/a)'
        
        future = self.dialogue_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        response = future.result()
        decision = response.decision.lower()
        
        self.get_logger().info(f'Decision recibida: "{decision}"')
        
        # Ahora buscar 'aleatorio' o 'secuencial'
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
        wp_idx = self.waypoint_indices[self.current_idx]
        waypoint = self.waypoints[wp_idx]
        
        goal = NavigateToWaypoint.Goal()
        goal.waypoint_name = waypoint['name']
        goal.x = float(waypoint['x'])
        goal.y = float(waypoint['y'])
        goal.z = float(waypoint['z'])
        goal.w = float(waypoint['w'])
        
        self.get_logger().info(
            f'Objetivo {self.current_idx + 1}/{len(self.waypoint_indices)}: {goal.waypoint_name}'
        )
        
        send_goal_future = self.nav_client.send_goal_async(
            goal,
            feedback_callback=self.navigation_feedback_callback
        )
        
        send_goal_future.add_done_callback(self.navigation_goal_response_callback)
    
    def navigation_feedback_callback(self, feedback_msg):
        """Callback de feedback durante navegacion"""
        feedback = feedback_msg.feedback
        if int(feedback.distance_remaining * 5) % 10 == 0:
            self.get_logger().info(f'Restante: {feedback.distance_remaining:.2f}m')
    
    def navigation_goal_response_callback(self, future):
        """Callback cuando se acepta el objetivo"""
        self.goal_handle = future.result()
        
        if not self.goal_handle.accepted:
            self.get_logger().error('Objetivo rechazado')
            return
        
        self.get_logger().info('Navegando... (Presiona ENTER para interrumpir)')
        self.transition_to(State.NAVEGANDO)
        
        get_result_future = self.goal_handle.get_result_async()
        get_result_future.add_done_callback(self.navigation_result_callback)
    
    def navigation_result_callback(self, future):
        """Callback cuando termina la navegacion"""
        # Solo procesar si no fue pausado
        if self.state == State.PAUSADO:
            return
        
        result = future.result().result
        
        if result.success:
            self.get_logger().info(f'Exito: {result.message}')
            self.transition_to(State.LLEGADO)
            self.ask_user_decision()
        else:
            self.get_logger().error(f'Fallo: {result.message}')
            self.ask_retry()
    
    def ask_retry(self):
        """Preguntar si reintentar tras fallo"""
        req = GetUserDecision.Request()
        req.prompt = 'Fallo en navegacion. Reintentar? (s/n)'
        
        future = self.dialogue_client.call_async(req)
        future.add_done_callback(self.retry_callback)
    
    def retry_callback(self, future):
        """Procesa decision de reintento"""
        response = future.result()
        
        if 's' in response.decision or 'continuar' in response.decision:
            self.send_navigation_goal()
        else:
            self.get_logger().info('Navegacion cancelada tras fallo')
            self.transition_to(State.CANCELADO)
    
    def ask_user_decision(self):
        """Pregunta al usuario que hacer tras llegar"""
        self.transition_to(State.PREGUNTANDO)
        
        req = GetUserDecision.Request()
        req.prompt = 'Continuar, repetir o cancelar? (c/r/x)'
        
        future = self.dialogue_client.call_async(req)
        future.add_done_callback(self.user_decision_callback)
    
    def user_decision_callback(self, future):
        """Procesa decision del usuario"""
        try:
            response = future.result()
            decision = response.decision.lower()
            
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
                    self.get_logger().info('Todos los waypoints completados!')
                    self.transition_to(State.IDLE)
        
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
    
    def run(self):
        """Bucle principal"""
        self.load_waypoints()
        
        # Esperar servicios
        self.get_logger().info('Esperando servicios...')
        self.nav_client.wait_for_server()
        self.dialogue_client.wait_for_service()
        self.get_logger().info('Servicios listos')
        
        # Preguntar modo
        self.ask_navigation_mode()
        
        # Iniciar navegacion
        self.current_idx = 0
        self.send_navigation_goal()
        
        rclpy.spin(self)

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
