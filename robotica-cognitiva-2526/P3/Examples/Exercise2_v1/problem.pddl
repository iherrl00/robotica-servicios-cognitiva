(define (problem exercise2-handoff)
  (:domain exercise0)
  (:objects
    robot1 robot2 - robot
    loc1 loc2 loc3 - location
    box1 - object
  )
  (:init
    (at-robot robot1 loc1)
    (at-robot robot2 loc1)
    (holding robot1 box1)
    (can-move robot2)
  )
  (:goal
    (and
      (at-robot robot1 loc1)
      (at-object box1 loc3)
    )
  )
)
