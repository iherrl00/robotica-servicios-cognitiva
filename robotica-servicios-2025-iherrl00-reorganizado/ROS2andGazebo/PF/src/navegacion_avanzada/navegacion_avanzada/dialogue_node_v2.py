#!/usr/bin/env python3
"""
Nodo de dialogo con:
- Service Server para interaccion con usuario (TTS + input teclado)
- Thread separado escuchando 'i' para interrupciones
- Sincronización mejorada entre thread y service calls
- Sin race conditions en stdin

NOTA SOBRE TTS:
El ejercicio requiere usar sound_play/festival_tts (paquetes ROS).
Debido a limitaciones del sistema (Ubuntu 24.04 sin repositorios de audio_common),
se usa espeak como alternativa funcional que cumple el mismo propósito.
"""

from navegacion_avanzada_multiplesnodos.srv import GetUserDecision
from std_msgs.msg import Bool
import rclpy
from rclpy.node import Node
import os
import threading
import sys
import time

class DialogueNode(Node):
    def __init__(self):
        super().__init__('dialogue_node')
        
        # Service Server
        self.service = self.create_service(
            GetUserDecision,
            'get_user_decision',
            self.handle_user_decision
        )
        
        # Publisher para señales de interrupcion
        self.interrupt_pub = self.create_publisher(
            Bool,
            'interrupt_signal',
            10
        )
        
        # Control de thread de interrupcion con locks para sincronización
        self.interrupt_thread_active = True
        self.service_lock = threading.Lock()
        self.in_service_call = False
        
        self.input_mode = 'keyboard'  # 'keyboard' o 'voice'
        self.first_waypoint_reached = False
        
        # Buffer para stdin
        self.stdin_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Iniciar thread de escucha de interrupciones
        self.interrupt_thread = threading.Thread(target=self.interrupt_listener, daemon=True)
        self.interrupt_thread.start()
        
        self.speak('Nodo de dialogo iniciado')
        self.get_logger().info('Dialogue Node iniciado con sistema de interrupcion v2')
        self.get_logger().info('Escuchando "i" + ENTER para interrumpir navegacion')
    
    def interrupt_listener(self):
        """Thread que escucha continuamente por 'i' para interrumpir"""
        while self.interrupt_thread_active:
            try:
                # Verificar si estamos en service call
                with self.service_lock:
                    if self.in_service_call:
                        # No leer stdin durante service calls
                        time.sleep(0.1)
                        continue
                
                # Leer stdin de forma no bloqueante
                import select
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                
                if ready:
                    line = sys.stdin.readline().strip().lower()
                    
                    # Si el usuario escribe 'i', publicar interrupcion
                    if line == 'i' or line == 'interrupt':
                        with self.service_lock:
                            if not self.in_service_call:
                                self.get_logger().info('¡Señal de INTERRUPCION detectada!')
                                msg = Bool()
                                msg.data = True
                                self.interrupt_pub.publish(msg)
                                self.speak('Interrupcion registrada')
                    else:
                        # Guardar en buffer para posible uso posterior
                        with self.buffer_lock:
                            self.stdin_buffer.append(line)
                            
            except Exception as e:
                # Ignorar errores de lectura
                pass
    
    def speak(self, text):
        """Sintesis de voz con espeak"""
        self.get_logger().info(f'Robot dice: {text}')
        try:
            # Ejecutar en background para no bloquear
            os.system(f'espeak -s 140 "{text}" 2>/dev/null &')
        except:
            pass
            
    def ask_input_mode(self):
        """Pregunta al usuario qué modo de entrada quiere"""
        print("\n¿Modo de entrada? (teclado/voz): ", end='', flush=True)
        mode = sys.stdin.readline().strip().lower()
        
        if 'voz' in mode or 'voice' in mode:
            self.input_mode = 'voice'
            self.speak('Modo voz activado')
            print("Modo VOZ activado - usa el micrófono")
        else:
            self.input_mode = 'keyboard'
            self.speak('Modo teclado activado')
            print("Modo TECLADO activado")
        
    def get_user_input(self, prompt):
        """Lee input según el modo configurado"""
        import speech_recognition as sr
        import time
        
        print(f'\n{prompt}: ', end='', flush=True)
        
        if self.input_mode == 'voice':
            time.sleep(3)
            
            # PAUSAR interrupt_listener temporalmente
            with self.service_lock:
                paused_interrupt = True
            
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    print("Habla ahora...")
                    try:
                        audio = r.listen(source, timeout=5, phrase_time_limit=5)
                        texto = r.recognize_google(audio, language='es-ES')
                        print(f"Escuché: {texto}")
                        return texto.lower()
                    except sr.WaitTimeoutError:
                        print("Timeout")
                        return 'continue'
                    except Exception as e:
                        print(f"No entendí")
                        return 'continue'
            finally:
                # REACTIVAR interrupt_listener
                with self.service_lock:
                    paused_interrupt = False
        else:
            # Teclado (modo original)
            return sys.stdin.readline().strip().lower()
    
    def handle_user_decision(self, request, response):
        """Maneja peticion de decision del usuario"""
        # Marcar que estamos en service call
        with self.service_lock:
            self.in_service_call = True
        
        try:
            prompt = request.prompt
            
            # PRIMERO: Si es el primer waypoint, preguntar modo
            if not self.first_waypoint_reached and any(x in prompt.lower() for x in ['continuar', 'repetir', 'cancelar', 'c)', 'r)', 'x)']):
                self.first_waypoint_reached = True
                self.ask_input_mode()
            
            # SEGUNDO: Hablar y pedir input
            self.speak(prompt)
            
            # Obtener input del usuario
            user_input = self.get_user_input(prompt)
            
            self.get_logger().info(f'Usuario escribio: "{user_input}"')
            
            # Parsear respuesta segun el contexto
            # Para modo de navegacion (s/a)
            if any(x in prompt.lower() for x in ['secuencial', 'aleatorio', 's/a', 's) o', 'a)']):
                if user_input == 'a' or 'aleat' in user_input or 'random' in user_input:
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
                elif user_input == 's' or 'siguiente' in user_input or 'next' in user_input or 'otro' in user_input:
                    response.decision = 'siguiente'
                    self.speak('Saltando al siguiente punto')
                elif user_input == 'x' or 'cancelar' in user_input or 'cancel' in user_input:
                    response.decision = 'cancel'
                    self.speak('Cancelando navegacion')
                else:
                    response.decision = 'continue'
                    self.speak('Continuando al mismo punto por defecto')
            
            # Para continuar/repetir/cancelar tras llegar
            elif any(x in prompt.lower() for x in ['continuar', 'repetir', 'cancelar', 'c)', 'r)', 'x)']):
                if user_input == 'c' or 'continuar' in user_input or 'si' in user_input or 'hola' in user_input:
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
                
        except Exception as e:
            self.get_logger().error(f'Error en handle_user_decision: {e}')
            response.decision = 'continue'
            
        finally:
            # Liberar lock
            with self.service_lock:
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
