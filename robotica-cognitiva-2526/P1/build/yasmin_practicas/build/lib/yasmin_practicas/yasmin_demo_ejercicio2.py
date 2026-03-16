#!/usr/bin/env python3

import time
import rclpy
import yasmin
from yasmin import State, Blackboard, StateMachine
from yasmin_ros import set_ros_loggers
from yasmin_viewer import YasminViewerPub

class FooState(State):
    def __init__(self) -> None:
        super().__init__(["outcome1", "outcome2"])
        self.counter = 0

    def execute(self, blackboard: Blackboard) -> str:
        yasmin.YASMIN_LOG_INFO("Executing state FOO")
        time.sleep(3)
        
        if self.counter < 3:
            self.counter += 1
            blackboard["foo_str"] = f"Counter: {self.counter}"
            return "outcome1"
        else:
            return "outcome2"

class BarState(State):
    def __init__(self) -> None:
        super().__init__(outcomes=["outcome3"])

    def execute(self, blackboard: Blackboard) -> str:
        yasmin.YASMIN_LOG_INFO("Executing state BAR")
        time.sleep(3)
        yasmin.YASMIN_LOG_INFO(blackboard["foo_str"])
        return "outcome3"

class BazState(State):
    """
    Nuevo estado BAZ que valida si el contador es par o impar
    """
    def __init__(self) -> None:
        super().__init__(outcomes=["outcome_par", "outcome_impar"])

    def execute(self, blackboard: Blackboard) -> str:
        yasmin.YASMIN_LOG_INFO("Executing state BAZ")
        time.sleep(2)
        
        # Extraer el valor del contador del string
        counter_str = blackboard["foo_str"]
        counter_value = int(counter_str.split(": ")[1])
        
        if counter_value % 2 == 0:
            yasmin.YASMIN_LOG_INFO(f"Contador {counter_value} es PAR")
            return "outcome_par"
        else:
            yasmin.YASMIN_LOG_INFO(f"Contador {counter_value} es IMPAR")
            return "outcome_impar"

def main() -> None:
    rclpy.init()
    set_ros_loggers()
    yasmin.YASMIN_LOG_INFO("yasmin_demo_ejercicio2")

    sm = StateMachine(outcomes=["outcome4"], handle_sigint=True)

    sm.add_state("FOO", FooState(), transitions={"outcome1": "BAR", "outcome2": "outcome4"})
    sm.add_state("BAR", BarState(), transitions={"outcome3": "BAZ"})
    sm.add_state("BAZ", BazState(), transitions={"outcome_par": "FOO", "outcome_impar": "FOO"})

    YasminViewerPub(sm, "YASMIN_DEMO_EJ2")

    try:
        outcome = sm()
        yasmin.YASMIN_LOG_INFO(outcome)
    except Exception as e:
        yasmin.YASMIN_LOG_WARN(e)

    if rclpy.ok():
        rclpy.shutdown()

if __name__ == "__main__":
    main()
