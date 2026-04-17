(define (domain waypoint-navigation)
  (:requirements :strips :typing)
  (:types waypoint robot)

  (:predicates
    (at ?r - robot ?w - waypoint)
    (connected ?w1 ?w2 - waypoint)
    (visited ?w - waypoint)
  )

  (:action move
    :parameters (?r - robot ?from ?to - waypoint)
    :precondition (and (at ?r ?from) (connected ?from ?to))
    :effect (and (not (at ?r ?from)) (at ?r ?to) (visited ?to))
  )
)
