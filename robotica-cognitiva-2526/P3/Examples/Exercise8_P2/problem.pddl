(define (problem robot-energy-problem)
  (:domain robot-energy)
  (:objects
    room1 room2 room3 - location
  )
  (:init
    (at room1)
    (connected room1 room2)
    (connected room2 room1)
    (connected room2 room3)
    (connected room3 room2)
    (charging-point room2)
    (= (battery) 1)
  )
  (:goal
    (at room3)
  )
)
