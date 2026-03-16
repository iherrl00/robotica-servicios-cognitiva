#!/usr/bin/env python3

import rclpy
from example_interfaces.action import Fibonacci

import yasmin
from yasmin import CbState, Blackboard, StateMachine
from yasmin_ros import ActionState
from yasmin_ros import set_ros_loggers
from yasmin_ros.basic_outcomes import SUCCEED, ABORT, CANCEL
from yasmin_viewer import YasminViewerPub


class FibonacciMonitorState(ActionState):
    """
    Estado Fibonacci con supervisión de valor máximo.
    Cancela la acción si algún valor supera el umbral.
    """

    def __init__(self, max_value: int) -> None:
        self.max_value = max_value
        self.cancelled = False
        super().__init__(
            Fibonacci,
            "/fibonacci",
            self.create_goal_handler,
            set(),
            self.response_handler,
            self.monitor_feedback,
        )

    def create_goal_handler(self, blackboard: Blackboard) -> Fibonacci.Goal:
        goal = Fibonacci.Goal()
        goal.order = blackboard["n"]
        self.cancelled = False  # Reset flag
        yasmin.YASMIN_LOG_INFO(f"Solicitando Fibonacci de orden {goal.order} con umbral máximo {self.max_value}")
        return goal

    def monitor_feedback(self, blackboard: Blackboard, feedback: Fibonacci.Feedback) -> None:
        """
        Supervisa el feedback y decide si cancelar
        """
        sequence = list(feedback.sequence)
        yasmin.YASMIN_LOG_INFO(f"Feedback recibido: {sequence}")
        
        # Verificar si algún valor supera el umbral
        if sequence and sequence[-1] > self.max_value:
            yasmin.YASMIN_LOG_WARN(f"¡ALERTA! Valor {sequence[-1]} supera el umbral {self.max_value}")
            yasmin.YASMIN_LOG_WARN("Cancelando la acción...")
            self.cancelled = True
            blackboard["cancel_reason"] = f"Valor {sequence[-1]} superó el umbral {self.max_value}"
            blackboard["last_sequence"] = sequence
            
            # Cancelar la acción
            self.cancel_state()

    def response_handler(self, blackboard: Blackboard, response: Fibonacci.Result) -> str:
        """
        Procesa el resultado
        """
        # Si ya marcamos como cancelado, retornar CANCEL
        if self.cancelled:
            yasmin.YASMIN_LOG_INFO("Acción fue cancelada")
            return CANCEL
        
        # Si llegamos aquí, la acción se completó exitosamente
        blackboard["fibo_res"] = response.sequence
        yasmin.YASMIN_LOG_INFO("Acción completada exitosamente")
        return SUCCEED


def print_result(blackboard: Blackboard) -> str:
    """Imprime el resultado completo"""
    yasmin.YASMIN_LOG_INFO("RESULTADO COMPLETO")
    yasmin.YASMIN_LOG_INFO(f"Secuencia: {blackboard['fibo_res']}")
    return SUCCEED


def print_cancelled(blackboard: Blackboard) -> str:
    """Imprime información de la cancelación"""
    yasmin.YASMIN_LOG_INFO("ACCIÓN CANCELADA")
    yasmin.YASMIN_LOG_INFO(f"Razón: {blackboard.get('cancel_reason', 'Desconocida')}")
    yasmin.YASMIN_LOG_INFO(f"Última secuencia recibida: {blackboard.get('last_sequence', [])}")
    return SUCCEED


def main() -> None:
    rclpy.init()
    set_ros_loggers()
    yasmin.YASMIN_LOG_INFO("yasmin_action_client_monitor_demo")

    # Crear FSM
    sm = StateMachine(outcomes=["outcome_success", "outcome_cancelled"], handle_sigint=True)

    # Añadir estados
    sm.add_state(
        "CALLING_FIBONACCI",
        FibonacciMonitorState(max_value=20),  # Umbral: 20
        transitions={
            SUCCEED: "PRINTING_RESULT",
            CANCEL: "PRINTING_CANCELLED",
            ABORT: "outcome_cancelled",
        },
    )
    sm.add_state(
        "PRINTING_RESULT",
        CbState([SUCCEED], print_result),
        transitions={SUCCEED: "outcome_success"},
    )
    sm.add_state(
        "PRINTING_CANCELLED",
        CbState([SUCCEED], print_cancelled),
        transitions={SUCCEED: "outcome_cancelled"},
    )

    YasminViewerPub(sm, "YASMIN_ACTION_MONITOR")

    # Blackboard inicial
    blackboard = Blackboard()
    blackboard["n"] = 15  # Fibonacci de orden 15

    try:
        outcome = sm(blackboard)
        yasmin.YASMIN_LOG_INFO(f"FSM terminó con: {outcome}")
    except KeyboardInterrupt:
        yasmin.YASMIN_LOG_INFO("Interrumpido por usuario")
    except Exception as e:
        yasmin.YASMIN_LOG_WARN(f"Error: {e}")

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
