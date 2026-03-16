#!/usr/bin/env python3
"""
Nodo de dialogo
Service Server para interaccion con usuario (TTS + input teclado)
"""

from navegacion_avanzada_multiplesnodos.srv import GetUserDecision
import rclpy
from rclpy.node import Node
import os

class DialogueNode(Node):
    def __init__(self):
        super().__init__('dialogue_node')
        
        # Service Server
        self.service = self.create_service(
            GetUserDecision,
            'get_user_decision',
            self.handle_user_decision
        )
        
        self.speak('Nodo de dialogo iniciado')
        self.get_logger().info('Dialogue Node iniciado')
    
    def speak(self, text):
        """Sintesis de voz con espeak"""
        self.get_logger().info(f'Robot dice: {text}')
        try:
            os.system(f'espeak -s 130 "{text}" 2>/dev/null')
        except:
            pass
    
    def handle_user_decision(self, request, response):
        """Maneja peticion de decision del usuario"""
        prompt = request.prompt
        
        # Hablar y pedir input
        self.speak(prompt)
        user_input = input(f'{prompt}: ').strip().lower()
        
        self.get_logger().info(f'Usuario escribio: "{user_input}"')
        
        # Parsear respuesta segun el contexto
        # Para modo de navegacion (s/a)
        if 's/a' in prompt.lower():
            if user_input == 'a' or 'aleat' in user_input or 'random' in user_input:
                response.decision = 'aleatorio'
                self.speak('Modo aleatorio activado')
            else:
                response.decision = 'secuencial'
                self.speak('Modo secuencial activado')
        
        # Para continuar/repetir/cancelar (c/r/x)
        elif 'c/r/x' in prompt.lower():
            if user_input == 'c' or 'continuar' in user_input or 'si' in user_input:
                response.decision = 'continue'
                self.speak('Entendido. Continuando')
            elif user_input == 'r' or 'repetir' in user_input:
                response.decision = 'repeat'
                self.speak('De acuerdo. Repitiendo')
            elif user_input == 'x' or 'cancelar' in user_input or 'no' in user_input:
                response.decision = 'cancel'
                self.speak('Entendido. Cancelando')
            else:
                response.decision = 'continue'
                self.speak('No entendi. Continuando por defecto')
        
        # Para interrupciones (c/o/x)
        elif 'c/o/x' in prompt.lower():
            if user_input == 'c' or 'continuar' in user_input or 'mismo' in user_input:
                response.decision = 'continue'
                self.speak('Continuando al mismo punto')
            elif user_input == 'o' or 'otro' in user_input or 'siguiente' in user_input:
                response.decision = 'otro'
                self.speak('Saltando al siguiente punto')
            elif user_input == 'x' or 'cancelar' in user_input:
                response.decision = 'cancel'
                self.speak('Cancelando navegacion')
            else:
                response.decision = 'continue'
                self.speak('No entendi. Continuando al mismo punto')
        
        # Para reintentos (s/n)
        elif 's/n' in prompt.lower():
            if user_input == 's' or 'si' in user_input:
                response.decision = 'continue'
                self.speak('Reintentando')
            else:
                response.decision = 'cancel'
                self.speak('Cancelando')
        
        else:
            # Caso generico
            response.decision = user_input
        
        return response

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
        
  
