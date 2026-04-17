"""
Exercise 7 — basic_pddl_node sin simulador
Ejecuta el planificador y muestra el plan sin necesitar Nav2 ni Tiago.
"""

import subprocess
import os

# Rutas
HOME = os.path.expanduser("~")
PACKAGE_PATH = HOME + "/pddl_ws/PDDL-course-main/Examples/Exercise7/src/my_pddl_package/"
SOLVER_PATH  = HOME + "/pddl_ws/PDDL-course-main/Planners/SMTPlan"
PATH_PDDL_FILES  = PACKAGE_PATH + "domains_and_problems"
DOMAIN_PDDL_FILE = "domain.pddl"
PROBLEM_PDDL_FILE = "problem.pddl"
PATH_FOLDER_WAYPOINTS = PACKAGE_PATH + "waypoints/"

# Mostrar dominio
domain_path  = os.path.join(PATH_PDDL_FILES, DOMAIN_PDDL_FILE)
problem_path = os.path.join(PATH_PDDL_FILES, PROBLEM_PDDL_FILE)

print("PDDL Domain:")
with open(domain_path, encoding="utf-8") as f:
    print(f.read())

print("PDDL Problem:")
with open(problem_path, encoding="utf-8") as f:
    print(f.read())

# Ejecutar planificador
print("Running SMTPlan...")

solver = subprocess.Popen(
    args=[SOLVER_PATH, domain_path, problem_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
stdout, stderr = solver.communicate()

# Parsear y mostrar plan
print("Raw planner output:")
print(stdout.decode())

print("Parsed navigation path:")

path = []
for line in stdout.decode().splitlines():
    line = line.strip()
    # SMTPlan output lines look like: "0.0:  (go-to kitchen corridor)"
    if "(go-to" in line.lower():
        parts = line.split()
        # Extract destination waypoint (last token before closing paren)
        action = line[line.find("(")+1 : line.find(")")]
        tokens = action.split()
        if len(tokens) >= 3:
            dest = tokens[2]
            path.append(dest)
            print(f"  → Navigate to: {dest}")

if not path:
    print("  (no go-to actions found in plan)")

# Mostrar waypoints disponibles
import yaml
waypoints_file = os.path.join(PATH_FOLDER_WAYPOINTS, "waypoints.yaml")
if os.path.exists(waypoints_file):
    print("Available waypoints (from waypoints.yaml):")
    with open(waypoints_file) as f:
        waypoints = yaml.safe_load(f)
    for name, data in waypoints.items():
        pos = data.get("position", {})
        print(f"  {name}: x={pos.get('x',0):.2f}, y={pos.get('y',0):.2f}")

    print("Plan execution (simulated — no Nav2):")
    for point in path:
        if point in waypoints:
            wp = waypoints[point]
            pos = wp.get("position", {})
            print(f"  [SEND GOAL] → {point}  "
                  f"(x={pos.get('x',0):.2f}, y={pos.get('y',0):.2f})")
            print(f"  [RESULT]    → SUCCEEDED (simulated)")
        else:
            print(f"  [WARN] Waypoint '{point}' not found in yaml")
else:
    print(f"(waypoints.yaml not found at {waypoints_file})")
