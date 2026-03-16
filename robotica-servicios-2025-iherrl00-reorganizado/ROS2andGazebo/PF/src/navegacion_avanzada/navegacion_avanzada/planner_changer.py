#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue

class PlannerChanger(Node):
    def __init__(self):
        super().__init__('planner_changer')
        
        # Cliente para cambiar parámetros del planner_server
        self.planner_client = self.create_client(
            SetParameters, 
            '/planner_server/set_parameters'
        )
        
        # Cliente para cambiar parámetros del controller_server
        self.controller_client = self.create_client(
            SetParameters,
            '/controller_server/set_parameters'
        )
        
        # Esperar a que los servicios estén disponibles
        self.get_logger().info('Esperando servicios de parámetros...')
        while not self.planner_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando planner_server...')
        
        while not self.controller_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando controller_server...')
        
        self.get_logger().info('Servicios disponibles')
    
    def set_planner(self, planner_name):
        """Cambia el planificador global"""
        req = SetParameters.Request()
        
        param = Parameter()
        param.name = 'planner_id'
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=planner_name
        )
        
        req.parameters = [param]
        
        future = self.planner_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            self.get_logger().info(f'✅ Planificador cambiado a: {planner_name}')
            return True
        else:
            self.get_logger().error(f'❌ Error al cambiar planificador a {planner_name}')
            return False
    
    def set_controller(self, controller_name):
        """Cambia el controlador local"""
        req = SetParameters.Request()
        
        param = Parameter()
        param.name = 'controller_id'
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=controller_name
        )
        
        req.parameters = [param]
        
        future = self.controller_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            self.get_logger().info(f'✅ Controlador cambiado a: {controller_name}')
            return True
        else:
            self.get_logger().error(f'❌ Error al cambiar controlador a {controller_name}')
            return False

def main(args=None):
    rclpy.init(args=args)
    
    changer = PlannerChanger()
    
    # Ejemplo de uso: cambiar entre planificadores
    print('\n=== Probando cambio de planificadores ===\n')
    
    # Cambiar a GridBased (NavFn)
    changer.set_planner('GridBased')
    
    import time
    time.sleep(2)
    
    # Cambiar a SmacPlanner
    changer.set_planner('SmacPlanner')
    
    time.sleep(2)
    
    # Cambiar controlador local
    changer.set_controller('DWB')
    
    changer.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
