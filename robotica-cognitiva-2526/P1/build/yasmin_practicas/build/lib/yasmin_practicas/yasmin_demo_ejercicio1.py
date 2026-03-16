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

def main() -> None:
    rclpy.init()
    set_ros_loggers()
    yasmin.YASMIN_LOG_INFO("yasmin_demo")

    sm = StateMachine(outcomes=["outcome4"], handle_sigint=True)

    sm.add_state("FOO", FooState(), transitions={"outcome1": "BAR", "outcome2": "outcome4"})
    sm.add_state("BAR", BarState(), transitions={"outcome3": "FOO"})

    YasminViewerPub(sm, "YASMIN_DEMO")

    try:
        outcome = sm()
        yasmin.YASMIN_LOG_INFO(outcome)
    except Exception as e:
        yasmin.YASMIN_LOG_WARN(e)

    if rclpy.ok():
        rclpy.shutdown()

if __name__ == "__main__":
    main()
