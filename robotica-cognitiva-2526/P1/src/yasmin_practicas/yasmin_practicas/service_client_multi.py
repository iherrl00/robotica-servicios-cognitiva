#!/usr/bin/env python3

import rclpy
from example_interfaces.srv import AddTwoInts

import yasmin
from yasmin import CbState, Blackboard, StateMachine
from yasmin_ros import ServiceState
from yasmin_ros import set_ros_loggers
from yasmin_ros.basic_outcomes import SUCCEED, ABORT
from yasmin_viewer import YasminViewerPub


class AddTwoIntsState(ServiceState):
    def __init__(self) -> None:
        super().__init__(
            AddTwoInts,
            "/add_two_ints",
            self.create_request_handler,
            ["outcome1"],
            self.response_handler,
        )

    def create_request_handler(self, blackboard: Blackboard) -> AddTwoInts.Request:
        req = AddTwoInts.Request()
        req.a = blackboard["current_a"]
        req.b = blackboard["current_b"]
        return req

    def response_handler(self, blackboard: Blackboard, response: AddTwoInts.Response) -> str:
        # Almacenar la respuesta en la lista
        blackboard["results"].append({
            "a": blackboard["current_a"],
            "b": blackboard["current_b"],
            "sum": response.sum
        })
        return "outcome1"


def init_data(blackboard: Blackboard) -> str:
    """Inicializa la lista de operaciones y resultados"""
    blackboard["operations"] = [
        (10, 5),
        (20, 15),
        (7, 3),
        (100, 50)
    ]
    blackboard["results"] = []
    blackboard["index"] = 0
    return SUCCEED


def prepare_next_request(blackboard: Blackboard) -> str:
    """Prepara los valores para la siguiente solicitud"""
    index = blackboard["index"]
    operations = blackboard["operations"]
    
    if index < len(operations):
        blackboard["current_a"], blackboard["current_b"] = operations[index]
        yasmin.YASMIN_LOG_INFO(f"Preparando solicitud {index + 1}: {blackboard['current_a']} + {blackboard['current_b']}")
        return SUCCEED
    else:
        return ABORT


def increment_counter(blackboard: Blackboard) -> str:
    """Incrementa el contador y decide si continuar"""
    blackboard["index"] += 1
    
    if blackboard["index"] < len(blackboard["operations"]):
        return "continue"  # Más operaciones pendientes
    else:
        return "done"  # Todas completadas


def print_all_results(blackboard: Blackboard) -> str:
    """Imprime todos los resultados almacenados"""
    yasmin.YASMIN_LOG_INFO("RESULTADOS DE TODAS LAS OPERACIONES")
    for i, result in enumerate(blackboard["results"], 1):
        yasmin.YASMIN_LOG_INFO(f"Operación {i}: {result['a']} + {result['b']} = {result['sum']}")
    return SUCCEED


def main() -> None:
    rclpy.init()
    set_ros_loggers()
    yasmin.YASMIN_LOG_INFO("yasmin_service_client_multi_demo")

    sm = StateMachine(outcomes=["outcome_final"], handle_sigint=True)

    sm.add_state("INIT_DATA", CbState([SUCCEED], init_data), transitions={SUCCEED: "PREPARE_REQUEST"})
    
    sm.add_state("PREPARE_REQUEST", CbState([SUCCEED, ABORT], prepare_next_request), 
                 transitions={SUCCEED: "CALL_SERVICE", ABORT: "PRINT_RESULTS"})
    
    sm.add_state("CALL_SERVICE", AddTwoIntsState(), 
                 transitions={"outcome1": "INCREMENT", SUCCEED: "INCREMENT", ABORT: "PRINT_RESULTS"})
    
    sm.add_state("INCREMENT", CbState(["continue", "done"], increment_counter), 
                 transitions={"continue": "PREPARE_REQUEST", "done": "PRINT_RESULTS"})
    
    sm.add_state("PRINT_RESULTS", CbState([SUCCEED], print_all_results), 
                 transitions={SUCCEED: "outcome_final"})

    YasminViewerPub(sm, "YASMIN_SERVICE_MULTI")

    try:
        outcome = sm()
        yasmin.YASMIN_LOG_INFO(outcome)
    except Exception as e:
        yasmin.YASMIN_LOG_WARN(e)

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
