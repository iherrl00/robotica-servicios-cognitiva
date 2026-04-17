(define (problem waypoint-problem)
  (:domain waypoint-navigation)
  (:objects
    robot1 - robot
    wp1 wp2 wp3 wp4 - waypoint
  )
  (:init
    (at robot1 wp1)
    (connected wp1 wp2)
    (connected wp2 wp1)
    (connected wp2 wp3)
    (connected wp3 wp2)
    (connected wp3 wp4)
    (connected wp4 wp3)
  )
  (:goal
    (and
      (at robot1 wp4)
      (visited wp2)
      (visited wp3)
      (visited wp4)
    )
  )
)
