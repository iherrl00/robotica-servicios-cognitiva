(define (domain robot-energy)
  (:requirements :strips :typing :fluents)
  (:types location)

  (:predicates
    (at ?l - location)
    (connected ?l1 ?l2 - location)
    (charging-point ?l - location)
  )

  (:functions
    (battery)
  )

  (:action move
    :parameters (?from ?to - location)
    :precondition (and
      (at ?from)
      (connected ?from ?to)
      (> (battery) 0)
    )
    :effect (and
      (not (at ?from))
      (at ?to)
      (decrease (battery) 1)
    )
  )

  (:action recharge
    :parameters (?l - location)
    :precondition (and
      (at ?l)
      (charging-point ?l)
    )
    :effect (and
      (assign (battery) 10)
    )
  )
)
