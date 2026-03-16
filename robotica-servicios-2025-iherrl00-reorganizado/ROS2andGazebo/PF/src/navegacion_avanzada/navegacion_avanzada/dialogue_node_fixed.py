#!/usr/bin/env python3
"""
Nodo de dialogo MEJORADO con:
- Service Server para interaccion con usuario (TTS + input teclado)
- Thread separado escuchando 'i' para interrupciones
- Publicacion de señal de interrupcion via topic
"""

from navegacion_avanzada_multiplesnodos.srv import GetUserDecision
from std_msgs.msg import Bool
import rclpy
from rclpy.node import Node
import os
import threading
import sys

class DialogueNode(Node):
    def __init__(self):
        super().__init__('dialogue_node')
        
        # Service Server
        self.service = self.create_service(
            GetUserDecision,
            'get_user_decision',
            self.handle_user_decision
        )
        
        # NUEVO: Publisher para señales de interrupcion
        self.interrupt_pub = self.create_publisher(
            Bool,
            'interrupt_signal',
            10
        )
        
        # Control de thread de interrupcion
        self.interrupt_thread_active = True
        self.in_service_call = False
        
        # Iniciar thread de escucha de interrupciones
        self.interrupt_thread = threading.Thread(target=self.interrupt_listener, daemon=True)
        self.interrupt_thread.start()
        
        self.speak('Nodo de dialogo iniciado')
        self.get_logger().info('Dialogue Node iniciado con sistema de interrupcion')
        self.get_logger().info('Escuchando "i" + ENTER para interrumpir navegacion')
    
    def interrupt_listener(self):
        """Thread que escucha continuamente por 'i' para interrumpir"""
        import select
        
        while self.interrupt_thread_active:
            try:
                # Solo leer si no estamos en medio de un service call
                if not self.in_service_call:
                    # Verificar si hay input disponible (timeout 0.5s)
                    ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                    
                    if ready:
                        line = sys.stdin.readline().strip().lower()
                        
                        # Si el usuario escribe 'i', publicar interrupcion
                        if line == 'i':
                            self.get_logger().info('¡Señal de INTERRUPCION detectada!')
                            msg = Bool()
                            msg.data = True
                            self.interrupt_pub.publish(msg)
                            self.speak('Interrupcion registrada')
                else:
                    # Pequeña pausa si estamos en service call
                    import time
                    time.sleep(0.1)
                    
            except Exception as e:
                # Ignorar errores de lectura
                pass
    
    def speak(self, text):
        """Sintesis de voz con espeak"""
        self.get_logger().info(f'Robot dice: {text}')
        try:
            os.system(f'espeak -s 140 "{text}" 2>/dev/null &')
        except:
            pass
    
    def handle_user_decision(self, request, response):
        """Maneja peticion de decision del usuario"""
        self.in_service_call = True
        
        try:
            prompt = request.prompt
            
            # Hablar y pedir input
            self.speak(prompt)
            print(f'\n{prompt}: ', end='', flush=True)
            user_input = input().strip().lower()
            
            self.get_logger().info(f'Usuario escribio: "{user_input}"')
            
            # Parsear respuesta segun el contexto
            if any(x in prompt.lower() for x in ['secuencial', 'aleatorio', 'manual', 's/a', 's)', 'a)', 'm)']):
                if user_input == 'm' or 'manual' in user_input:
                    response.decision = 'manual'
                    self.speak('Modo manual activado')
                elif user_input == 'a' or 'aleat' in user_input or 'random' in user_input:
                    response.decision = 'aleatorio'
                    self.speak('Modo aleatorio activado')
                else:
                    response.decision = 'secuencial'
                    self.speak('Modo secuencial activado')
            
            # Para interrupciones (continuar/siguiente/cancelar)
            elif any(x in prompt.lower() for x in ['interrumpida', 'mismo punto', 'siguiente']):
                if user_input == 'c' or 'continuar' in user_input or 'mismo' in user_input:
                    response.decision = 'continue'
                    self.speak('Continuando al mismo punto')
                elif user_input == 's' or 'siguiente' in user_input or 'next' in user_input:
                    response.decision = 'siguiente'
                    self.speak('Saltando al siguiente punto')
                elif user_input == 'x' or 'cancelar' in user_input:
                    response.decision = 'cancel'
                    self.speak('Cancelando navegacion')
                else:
                    response.decision = 'continue'
                    self.speak('Continuando al mismo punto por defecto')
            
            # Para continuar/repetir/cancelar tras llegar
            elif any(x in prompt.lower() for x in ['continuar', 'repetir', 'cancelar', 'c)', 'r)', 'x)']):
                if user_input == 'c' or 'continuar' in user_input or 'si' in user_input:
                    response.decision = 'continue'
                    self.speak('Entendido. Continuando')
                elif user_input == 'r' or 'repetir' in user_input or 'repeat' in user_input:
                    response.decision = 'repeat'
                    self.speak('De acuerdo. Repitiendo')
                elif user_input == 'x' or 'cancelar' in user_input or 'no' in user_input:
                    response.decision = 'cancel'
                    self.speak('Entendido. Cancelando')
                else:
                    response.decision = 'continue'
                    self.speak('Continuando por defecto')
            
            # Para reintentos (s/n)
            elif 's/n' in prompt.lower() or 'reintentar' in prompt.lower():
                if user_input == 's' or 'si' in user_input or 'yes' in user_input:
                    response.decision = 'continue'
                    self.speak('Reintentando')
                else:
                    response.decision = 'cancel'
                    self.speak('Cancelando')
            
            else:
                # Caso generico
                response.decision = user_input
                
        finally:
            self.in_service_call = False
        
        return response
    
    def destroy_node(self):
        """Limpieza al destruir el nodo"""
        self.interrupt_thread_active = False
        super().destroy_node()

def main():
    rclpy.init()
    node = DialogueNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
