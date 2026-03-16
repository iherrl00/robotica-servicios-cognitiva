#!/usr/bin/env python3

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.node import Node
import yaml
import time
import os
import random
from ament_index_python.packages import get_package_share_directory


class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('waypoint_navigator')
        
        self.navigator = BasicNavigator()
        self.get_logger().info('Waypoint Navigator inicializado')
        
        # Variables de control
        self.waypoints = []
        self.current_waypoint_idx = 0
        self.mode = 'sequential'  # 'sequential' o 'random'
        
    def read_waypoints(self, file_path):
        """Lee los waypoints desde un archivo YAML"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                self.waypoints = data.get('waypoints', [])
                self.get_logger().info(f'Cargados {len(self.waypoints)} waypoints')
                return True
        except Exception as e:
            self.get_logger().error(f'Error al leer waypoints: {str(e)}')
            return False
    
    def create_pose_stamped(self, waypoint):
        """Crea un PoseStamped desde un waypoint"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = float(waypoint['x'])
        pose.pose.position.y = float(waypoint['y'])
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = float(waypoint['z'])
        pose.pose.orientation.w = float(waypoint['w'])
        return pose
    
    def speak(self, message):
        """Simula síntesis de voz (puedes reemplazar con festival_tts o sound_play)"""
        self.get_logger().info(f'Robot dice: {message}')
        print(f'\n*** {message} ***\n')
    
    def get_user_input(self, prompt):
        """Obtiene input del usuario por teclado (alternativa a reconocimiento de voz)"""
        self.get_logger().info(f'  {prompt}')
        return input(f'{prompt}: ').strip().lower()
    
    def navigate_sequential(self):
        """Navega por los waypoints secuencialmente"""
        self.speak('Iniciando navegación secuencial')
        
        for idx, wp in enumerate(self.waypoints):
            self.get_logger().info(f'--- Waypoint {idx + 1}/{len(self.waypoints)}: {wp["name"]} ---')
            
            goal_pose = self.create_pose_stamped(wp)
            
            # Enviar objetivo
            self.navigator.goToPose(goal_pose)
            
            # Monitorear progreso
            while not self.navigator.isTaskComplete():
                feedback = self.navigator.getFeedback()
                if feedback:
                    remaining = feedback.distance_remaining
                    self.get_logger().info(f'Distancia restante: {remaining:.2f} m')
                time.sleep(1)
            
            # Verificar resultado
            result = self.navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                self.speak(f'He llegado al punto {wp["name"]}')
                
                # Solicitar confirmación para continuar
                response = self.get_user_input('¿Continuar al siguiente punto? (s/n/r=repetir)')
                
                if response == 'n':
                    self.speak('Navegación detenida por el usuario')
                    break
                elif response == 'r':
                    self.get_logger().info('Repitiendo waypoint actual')
                    continue
                else:
                    self.speak('Continuando al siguiente punto')
            else:
                self.speak(f'No pude llegar al punto {wp["name"]}')
                retry = self.get_user_input('¿Reintentar este punto? (s/n)')
                if retry != 's':
                    break
        
        self.speak('Navegación completada')
    
    def navigate_random(self):
        """Navega por los waypoints en orden aleatorio"""
        self.speak('Iniciando navegación aleatoria')
        
        indices = list(range(len(self.waypoints)))
        random.shuffle(indices)
        
        for count, idx in enumerate(indices):
            wp = self.waypoints[idx]
            self.get_logger().info(f'--- Waypoint aleatorio {count + 1}/{len(self.waypoints)}: {wp["name"]} ---')
            
            goal_pose = self.create_pose_stamped(wp)
            self.navigator.goToPose(goal_pose)
            
            while not self.navigator.isTaskComplete():
                feedback = self.navigator.getFeedback()
                if feedback:
                    self.get_logger().info(f'Distancia restante: {feedback.distance_remaining:.2f} m')
                time.sleep(1)
            
            result = self.navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                self.speak(f'Punto {wp["name"]} alcanzado')
            else:
                self.speak(f'Fallo en punto {wp["name"]}')
                break
        
        self.speak('Navegación aleatoria completada')


def main(args=None):
    rclpy.init(args=args)
    
    nav_node = WaypointNavigator()
    
    # Esperar a que Nav2 esté listo
    nav_node.get_logger().info('Esperando a que Nav2 esté activo...')
    nav_node.navigator.waitUntilNav2Active()
    nav_node.get_logger().info('Nav2 está listo')
    
    # Leer waypoints usando get_package_share_directory
    package_share_directory = get_package_share_directory('navegacion_avanzada')
    waypoints_path = os.path.join(package_share_directory, 'config', 'waypoints.yaml')
    
    if not nav_node.read_waypoints(waypoints_path):
        nav_node.get_logger().error('No se pudieron cargar los waypoints')
        rclpy.shutdown()
        return
    
    # Preguntar modo de navegación
    nav_node.speak('Sistema de navegación iniciado')
    mode = nav_node.get_user_input('Modo de navegación: (s)ecuencial o (r)andom?')
    
    try:
        if mode == 'r':
            nav_node.navigate_random()
        else:
            nav_node.navigate_sequential()
    except KeyboardInterrupt:
        nav_node.get_logger().info('Navegación interrumpida por el usuario')
    except Exception as e:
        nav_node.get_logger().error(f'Error durante la navegación: {str(e)}')
    finally:
        nav_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

