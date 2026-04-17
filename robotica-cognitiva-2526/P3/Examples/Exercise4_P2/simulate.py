plan = [
    ("move", "robot1", "wp1", "wp2"),
    ("move", "robot1", "wp2", "wp3"),
    ("move", "robot1", "wp3", "wp4"),
]

position = "wp1"
visited = {"wp1"}

print("SIMULACION DE NAVEGACION POR WAYPOINTS")
print(f"Estado inicial: robot1 en {position}\n")

for i, action in enumerate(plan):
    _, robot, from_wp, to_wp = action
    print(f"Paso {i}: MOVE {robot} {from_wp} -> {to_wp}")
    print(f"  [Precondicion] robot en {from_wp}: {position == from_wp}")
    position = to_wp
    visited.add(to_wp)
    print(f"  [Efecto] robot ahora en {position}")
    print(f"  [Visitados] {visited}\n")

print(f"FIN: robot en {position}")
print(f"Waypoints visitados: {visited}")
