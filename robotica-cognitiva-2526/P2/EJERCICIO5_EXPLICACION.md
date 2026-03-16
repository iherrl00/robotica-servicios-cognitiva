# Ejercicio 5 - Behavior Tree para Robot Doméstico

## XML del árbol

```xml
<?xml version="1.0"?>
<root main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <Fallback name="RobotBehavior">

      <!-- Si batería baja → volver a base -->
      <Sequence name="LowBatteryRecovery">
        <Condition ID="IsBatteryLow" name="¿Batería baja?"/>
        <Action ID="ReturnToBase" name="Volver a base"/>
      </Sequence>

      <!-- Comportamiento normal -->
      <Sequence name="NormalBehavior">
        <Condition ID="IsBatteryOK" name="¿Batería OK?"/>
        <Fallback name="NavigationWithObstacleAvoidance">
          <Sequence name="ObstacleAvoidance">
            <Condition ID="IsObstacleDetected" name="¿Hay obstáculo?"/>
            <Action ID="Stop" name="Detenerse"/>
            <Action ID="Turn" name="Girar"/>
          </Sequence>
          <Action ID="NavigateToWaypoint" name="Navegar a waypoint"/>
        </Fallback>
      </Sequence>

    </Fallback>
  </BehaviorTree>
</root>
```

## Estructura del árbol

```
Fallback [RobotBehavior]
├── Sequence [LowBatteryRecovery]
│   ├── Condition: IsBatteryLow
│   └── Action: ReturnToBase
└── Sequence [NormalBehavior]
    ├── Condition: IsBatteryOK
    └── Fallback [NavigationWithObstacleAvoidance]
        ├── Sequence [ObstacleAvoidance]
        │   ├── Condition: IsObstacleDetected
        │   ├── Action: Stop
        │   └── Action: Turn
        └── Action: NavigateToWaypoint
```

## Explicación del funcionamiento

### Nodo raíz: Fallback [RobotBehavior]

En cada tick, el árbol evalúa primero la rama de batería baja y luego el comportamiento normal. El Fallback garantiza que siempre se ejecute algún comportamiento válido.

### Rama 1: LowBatteryRecovery (Sequence)

Comprueba primero si la batería está baja (`IsBatteryLow`):
- Si la batería **está baja** → la condición devuelve SUCCESS → se ejecuta `ReturnToBase` → el Sequence devuelve SUCCESS → el Fallback raíz para (prioridad máxima).
- Si la batería **no está baja** → la condición devuelve FAILURE → el Sequence devuelve FAILURE → el Fallback pasa a la rama 2.

### Rama 2: NormalBehavior (Sequence)

Comprueba que la batería esté en buen estado (`IsBatteryOK`) y luego ejecuta la navegación:
- Si la batería está OK → pasa al Fallback de navegación.
- Dentro del Fallback de navegación:
  - Primero intenta la secuencia de **evitación de obstáculos**: si hay obstáculo → detener → girar.
  - Si no hay obstáculo (el Sequence falla en `IsObstacleDetected`) → **navega al waypoint** directamente.

## Comportamientos cubiertos

| Situación | Comportamiento |
|-----------|---------------|
| Batería baja | Vuelve a la base inmediatamente |
| Obstáculo detectado | Se detiene y gira para evitarlo |
| Camino libre | Navega al waypoint objetivo |
