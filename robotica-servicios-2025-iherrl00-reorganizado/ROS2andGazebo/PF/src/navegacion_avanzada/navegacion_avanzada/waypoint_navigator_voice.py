#!/usr/bin/env python3
"""
Navegador con VOZ usando espeak + speech_recognition
"""

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.node import Node
import yaml
import time
import os
import random
import subprocess

class VoiceNavigator(Node):
    def __init__(self):
        super().__init__('voice_navigator')
        self.navigator = BasicNavigator()
        self.waypoints = []
        self.get_logger().info('🤖 Voice Navigator iniciado')
    
    def speak(self, text):
        """TTS con espeak"""
        self.get_logger().info(f'🔊 {text}')
        try:
            # SIN & al final para que espere a terminar
            os.system(f'espeak -s 130 "{text}" 2>/dev/null')
        except:
            pass
    
    def listen(self, prompt=""):
        """Input por teclado (fallback)"""
        if prompt:
            self.speak(prompt)
        return input(f'👤 {prompt}: ').strip().lower()
    
    def parse_command(self, text):
        if any(w in text for w in ['si', 'continuar', 'siguiente', 's']):
            return 's'
        if any(w in text for w in ['no', 'detener', 'parar', 'n']):
            return 'n'
        if any(w in text for w in ['repetir', 'otra', 'r']):
            return 'r'
        return 's'
    
    def read_waypoints(self, path):
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                self.waypoints = data.get('waypoints', [])
                return True
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
            return False
    
    def create_pose(self, wp):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = float(wp['x'])
        pose.pose.position.y = float(wp['y'])
        pose.pose.orientation.z = float(wp['z'])
        pose.pose.orientation.w = float(wp['w'])
        return pose
    
    def navigate(self):
        self.speak('Sistema de navegacion iniciado')
        
        response = self.listen('Modo secuencial o aleatorio? (s/a)')
        
        if 'a' in response:
            indices = list(range(len(self.waypoints)))
            random.shuffle(indices)
            self.speak('Modo aleatorio')
        else:
            indices = list(range(len(self.waypoints)))
            self.speak('Modo secuencial')
        
        for count, idx in enumerate(indices):
            wp = self.waypoints[idx]
            self.speak(f'Navegando a {wp["name"]}')
            
            self.navigator.goToPose(self.create_pose(wp))
            
            while not self.navigator.isTaskComplete():
                time.sleep(0.5)
            
            if self.navigator.getResult() == TaskResult.SUCCEEDED:
                self.speak(f'Llegue a {wp["name"]}')
                
                if count < len(indices) - 1:
                    cmd = self.parse_command(
                        self.listen('Continuar, repetir o detener? (c/r/d)')
                    )
                    
                    if cmd == 'n':
                        self.speak('Deteniendo')
                        break
                    elif cmd == 'r':
                        self.speak('Repitiendo')
                        indices.insert(count + 1, idx)
            else:
                self.speak('Fallo en navegacion')
                break
        
        self.speak('Navegacion completada')

def main():
    rclpy.init()
    nav = VoiceNavigator()
    
    nav.speak('Esperando Nav2')
    nav.navigator.waitUntilNav2Active()
    nav.speak('Nav2 listo')
    
    wp_path = os.path.join(
        get_package_share_directory('navegacion_avanzada'),
        'config', 'waypoints.yaml'
    )
    
    if nav.read_waypoints(wp_path):
        nav.speak(f'{len(nav.waypoints)} waypoints cargados')
        try:
            nav.navigate()
        except KeyboardInterrupt:
            nav.speak('Interrumpido')
    
    nav.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
