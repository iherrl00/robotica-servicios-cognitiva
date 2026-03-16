#!/usr/bin/env python3

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
import rclpy
from rclpy.node import Node
import yaml
import time
import os
import random

class CompleteNavigator(Node):
    def __init__(self):
        """
        Constructor del nodo navegador completo.
        Inicializa el navegador, clientes de servicios y variables de estado.
        """
        super().__init__('complete_navigator')
        
        # Inicializar el navegador de Nav2
        self.navigator = BasicNavigator()
        
        # Lista para almacenar waypoints cargados desde YAML
        self.waypoints = []
        
        # Cliente para cambiar planificadores globales (planner_server)
        self.planner_client = self.create_client(
            SetParameters, 
            '/planner_server/set_parameters'
        )
        
        # Cliente para cambiar controladores locales (controller_server)
        self.controller_client = self.create_client(
            SetParameters,
            '/controller_server/set_parameters'
        )
        
        # Variables para tracking del estado del sistema
        self.current_planner = 'GridBased'  # Planificador actual
        self.current_controller = 'FollowPath'  # Controlador actual
        self.stuck_counter = 0  # Contador para detectar si esta atascado
        self.last_distance = None  # Ultima distancia registrada
        
        self.get_logger().info('Complete Navigator iniciado')
    
    def speak(self, text):
        """
        Sintesis de voz usando espeak.
        
        Args:
            text (str): Texto que el robot debe pronunciar
        """
        # Registrar en el log lo que el robot dira
        self.get_logger().info(f'Robot dice: {text}')
        
        try:
            # Ejecutar espeak con velocidad reducida (130 wpm)
            # 2>/dev/null: suprimir mensajes de error
            # Sin '&' para que espere a terminar antes de continuar
            os.system(f'espeak -s 130 "{text}" 2>/dev/null')
        except:
            # Si falla espeak, continuar sin error
            pass
    
    def listen(self, prompt=""):
        """
        Obtener input del usuario por teclado.
        Alternativa a reconocimiento de voz (STT).
        
        Args:
            prompt (str): Mensaje a mostrar al usuario
            
        Returns:
            str: Respuesta del usuario en minusculas
        """
        # Si hay un prompt, hacer que el robot lo pronuncie
        if prompt:
            self.speak(prompt)
        
        # Obtener input del usuario y convertir a minusculas
        return input(f'Usuario: {prompt}: ').strip().lower()
    
    def parse_command(self, text):
        """
        Interpreta el comando escrito por el usuario.
        
        Args:
            text (str): Texto introducido por el usuario
            
        Returns:
            str: 's' (continuar), 'n' (detener), 'r' (repetir)
        """
        # Palabras clave para continuar
        if any(w in text for w in ['si', 'continuar', 'siguiente', 's', 'c']):
            return 's'
        
        # Palabras clave para detener
        if any(w in text for w in ['no', 'detener', 'parar', 'n', 'd']):
            return 'n'
        
        # Palabras clave para repetir
        if any(w in text for w in ['repetir', 'otra', 'r']):
            return 'r'
        
        # Por defecto, continuar
        return 's'
    
    def change_planner(self, planner_name):
        """
        Cambia el planificador global de Nav2 dinamicamente.
        
        Args:
            planner_name (str): Nombre del planificador ('GridBased' o 'SmacPlanner')
        """
        # Si ya esta usando ese planificador, no hacer nada
        if planner_name == self.current_planner:
            return
        
        # Verificar que el servicio este disponible (timeout 1 segundo)
        if not self.planner_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('Servicio planner no disponible')
            return
        
        # Crear peticion de cambio de parametro
        req = SetParameters.Request()
        param = Parameter()
        param.name = 'planner_id'  # Nombre del parametro a cambiar
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=planner_name  # Nuevo valor del planificador
        )
        req.parameters = [param]
        
        # Llamar al servicio de forma asincrona
        future = self.planner_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        
        # Si el cambio fue exitoso, actualizar estado interno
        if future.result():
            self.current_planner = planner_name
            self.get_logger().info(f'Planificador cambiado a: {planner_name}')
            self.speak(f'Cambiando a planificador {planner_name}')
    
    def change_controller(self, controller_name):
        """
        Cambia el controlador local de Nav2 dinamicamente.
        
        Args:
            controller_name (str): Nombre del controlador
        """
        # Si ya esta usando ese controlador, no hacer nada
        if controller_name == self.current_controller:
            return
        
        # Verificar disponibilidad del servicio
        if not self.controller_client.wait_for_service(timeout_sec=1.0):
            return
        
        # Crear peticion de cambio de parametro
        req = SetParameters.Request()
        param = Parameter()
        param.name = 'controller_id'
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=controller_name
        )
        req.parameters = [param]
        
        # Llamar al servicio
        future = self.controller_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        
        # Actualizar estado si fue exitoso
        if future.result():
            self.current_controller = controller_name
            self.get_logger().info(f'Controlador cambiado a: {controller_name}')
    
    def detect_stuck(self, current_distance):
        """
        Detecta si el robot esta atascado comparando distancias.
        
        Args:
            current_distance (float): Distancia actual al objetivo
            
        Returns:
            bool: True si el robot parece estar atascado
        """
        # En la primera iteracion, solo guardar la distancia
        if self.last_distance is None:
            self.last_distance = current_distance
            return False
        
        # Si la distancia casi no cambia (menos de 5cm)
        if abs(current_distance - self.last_distance) < 0.05:
            self.stuck_counter += 1  # Incrementar contador
        else:
            self.stuck_counter = 0  # Reset si hay movimiento
        
        # Actualizar distancia previa
        self.last_distance = current_distance
        
        # Si lleva 10 iteraciones sin avanzar (aprox 5 segundos)
        if self.stuck_counter >= 10:
            self.get_logger().warn('Robot parece atascado')
            return True
        
        return False
    
    def smart_navigate(self, goal_pose, waypoint_name):
        """
        Navegacion inteligente con cambio automatico de planificadores.
        
        Criterios de cambio:
        1. Distancia > 0.5m: Usa GridBased (rapido para trayectorias largas)
        2. Distancia < 0.3m: Usa SmacPlanner (preciso para aproximacion final)
        3. Robot atascado: Alterna planificador para intentar nueva estrategia
        
        Args:
            goal_pose (PoseStamped): Pose objetivo a alcanzar
            waypoint_name (str): Nombre del waypoint (para logging)
            
        Returns:
            TaskResult: Resultado de la navegacion (SUCCEEDED, FAILED, etc)
        """
        self.get_logger().info(f'Navegando a: {waypoint_name}')
        
        # Enviar objetivo al navegador de Nav2
        self.navigator.goToPose(goal_pose)
        
        # Resetear variables de tracking
        self.stuck_counter = 0
        self.last_distance = None
        planner_changed_once = False  # Flag para evitar cambios repetidos
        
        # Loop mientras la tarea no este completa
        while not self.navigator.isTaskComplete():
            # Obtener feedback del navegador
            feedback = self.navigator.getFeedback()
            
            if feedback:
                # Distancia restante al objetivo
                remaining = feedback.distance_remaining
                
                # CRITERIO 1: Distancia media-larga (> 0.5m) - Usar GridBased
                if remaining > 0.5 and not planner_changed_once:
                    if self.current_planner != 'GridBased':
                        self.get_logger().info('Distancia media, usando GridBased')
                        self.change_planner('GridBased')
                        planner_changed_once = True  # Marcar que ya se cambio una vez
                
                # CRITERIO 2: Cerca del objetivo (< 0.3m) - Usar SmacPlanner
                elif remaining < 0.3:
                    if self.current_planner != 'SmacPlanner':
                        self.get_logger().info('Cerca del objetivo, usando SmacPlanner')
                        self.change_planner('SmacPlanner')
                
                # CRITERIO 3: Robot atascado - Alternar planificador
                if self.detect_stuck(remaining):
                    self.get_logger().warn('Robot atascado, cambiando estrategia')
                    self.speak('Estoy atascado, cambiando estrategia')
                    
                    # Alternar entre planificadores
                    if self.current_planner == 'GridBased':
                        self.change_planner('SmacPlanner')
                    else:
                        self.change_planner('GridBased')
                    
                    # Reset contador de atascamiento
                    self.stuck_counter = 0
                
                # Logging periodico cada 3 segundos
                if int(time.time()) % 3 == 0:
                    self.get_logger().info(
                        f'Distancia: {remaining:.2f}m | Planner: {self.current_planner}'
                    )
            
            # Esperar 0.5 segundos antes de siguiente iteracion
            time.sleep(0.5)
        
        # Retornar resultado final de la navegacion
        return self.navigator.getResult()
    
    def read_waypoints(self, path):
        """
        Lee waypoints desde archivo YAML.
        
        Args:
            path (str): Ruta al archivo waypoints.yaml
            
        Returns:
            bool: True si se cargaron correctamente, False si hubo error
        """
        try:
            # Abrir y parsear archivo YAML
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                # Extraer lista de waypoints
                self.waypoints = data.get('waypoints', [])
                self.get_logger().info(f'{len(self.waypoints)} waypoints cargados')
                return True
        except Exception as e:
            # Logging de error si falla la carga
            self.get_logger().error(f'Error al cargar waypoints: {e}')
            return False
    
    def create_pose(self, wp):
        """
        Crea un mensaje PoseStamped desde un waypoint del YAML.
        
        Args:
            wp (dict): Diccionario con claves 'x', 'y', 'z', 'w'
            
        Returns:
            PoseStamped: Mensaje de pose para Nav2
        """
        pose = PoseStamped()
        pose.header.frame_id = 'map'  # Frame de referencia
        pose.header.stamp = self.navigator.get_clock().now().to_msg()  # Timestamp actual
        
        # Posicion (x, y en el plano)
        pose.pose.position.x = float(wp['x'])
        pose.pose.position.y = float(wp['y'])
        
        # Orientacion (quaternion - solo z y w para rotacion 2D)
        pose.pose.orientation.z = float(wp['z'])
        pose.pose.orientation.w = float(wp['w'])
        
        return pose
    
    def navigate(self):
        """
        Funcion principal de navegacion.
        Gestiona el flujo completo: modo de navegacion, recorrido de waypoints,
        interaccion con usuario y cambio inteligente de planificadores.
        """
        # Anunciar inicio del sistema
        self.speak('Sistema de navegacion avanzada iniciado')
        
        # Preguntar modo de navegacion al usuario
        response = self.listen('Modo secuencial o aleatorio? (s/a)')
        
        # Determinar orden de navegacion
        if 'a' in response:
            # Modo aleatorio: mezclar indices
            indices = list(range(len(self.waypoints)))
            random.shuffle(indices)
            self.speak('Modo aleatorio activado')
        else:
            # Modo secuencial: orden original
            indices = list(range(len(self.waypoints)))
            self.speak('Modo secuencial activado')
        
        # Iterar por cada waypoint segun el orden establecido
        for count, idx in enumerate(indices):
            wp = self.waypoints[idx]
            
            # Anunciar objetivo actual
            self.speak(f'Objetivo numero {count + 1}: {wp["name"]}')
            
            # Navegar con cambio inteligente de planificadores
            result = self.smart_navigate(self.create_pose(wp), wp["name"])
            
            # Verificar resultado de la navegacion
            if result == TaskResult.SUCCEEDED:
                # Exito: anunciar llegada
                self.speak(f'He llegado a {wp["name"]}')
                
                # Si no es el ultimo waypoint, preguntar accion siguiente
                if count < len(indices) - 1:
                    cmd = self.parse_command(
                        self.listen('Continuar, repetir o detener? (c/r/d)')
                    )
                    
                    if cmd == 'n':
                        # Usuario decide detener
                        self.speak('Deteniendo navegacion')
                        break
                    elif cmd == 'r':
                        # Usuario decide repetir este waypoint
                        self.speak('Repitiendo este punto')
                        indices.insert(count + 1, idx)  # Insertar waypoint de nuevo
                    else:
                        # Continuar al siguiente
                        self.speak('Continuando')
            else:
                # Fallo en navegacion
                self.speak(f'No pude llegar a {wp["name"]}')
                
                # Preguntar si reintentar
                retry = self.listen('Reintentar este punto? (s/n)')
                if 's' in retry:
                    self.speak('Reintentando')
                    indices.insert(count + 1, idx)  # Reintentar waypoint
                else:
                    # Cancelar navegacion
                    break
        
        # Anunciar finalizacion
        self.speak('Navegacion completada. Mision finalizada')

def main():
    """
    Funcion principal del programa.
    Inicializa ROS2, crea el nodo navegador y ejecuta la navegacion.
    """
    # Inicializar sistema ROS2
    rclpy.init()
    
    # Crear instancia del navegador
    nav = CompleteNavigator()
    
    # Anunciar espera de Nav2
    nav.speak('Esperando sistema de navegacion')
    nav.get_logger().info('Esperando Nav2...')
    
    # Bloquear hasta que Nav2 este activo
    nav.navigator.waitUntilNav2Active()
    
    # Anunciar que Nav2 esta listo
    nav.speak('Sistema Nav2 activo')
    nav.get_logger().info('Nav2 listo')
    
    # Obtener ruta al archivo de waypoints
    wp_path = os.path.join(
        get_package_share_directory('navegacion_avanzada'),
        'config', 'waypoints.yaml'
    )
    
    # Cargar waypoints desde archivo
    if nav.read_waypoints(wp_path):
        # Anunciar cantidad de waypoints cargados
        nav.speak(f'Cargados {len(nav.waypoints)} puntos de ruta')
        
        try:
            # Ejecutar navegacion principal
            nav.navigate()
        except KeyboardInterrupt:
            # Manejo de interrupcion por teclado (Ctrl+C)
            nav.speak('Navegacion interrumpida por usuario')
            nav.get_logger().info('Interrumpido por usuario')
    else:
        # Error al cargar waypoints
        nav.speak('Error al cargar waypoints')
    
    # Limpiar y cerrar nodo
    nav.destroy_node()
    rclpy.shutdown()

# Punto de entrada del programa
if __name__ == '__main__':
    main()
