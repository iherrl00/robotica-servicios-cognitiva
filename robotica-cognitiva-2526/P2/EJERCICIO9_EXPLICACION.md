# Ejercicio 9 - Extensión del Behavior Tree con comprobación de batería

## Comportamiento esperado

- Si batería baja → volver a base (prioridad máxima)
- Si no → ejecutar comportamiento normal (evitar obstáculos o navegar)

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

## Flujo de ejecución observado

### Caso 1: Batería OK + obstáculo detectado
1. `Fallback` evalúa `LowBatteryRecovery`
2. `IsBatteryLow` → **FAILURE** → Sequence falla → Fallback pasa a rama 2
3. `IsBatteryOK` → **SUCCESS**
4. `IsObstacleDetected` → **SUCCESS**
5. `Stop` → SUCCESS, `Turn` → SUCCESS
6. Resultado: **DETENERSE + GIRAR**

### Caso 2: Batería OK + sin obstáculo
1. `IsBatteryLow` → **FAILURE** → pasa a rama 2
2. `IsBatteryOK` → **SUCCESS**
3. `IsObstacleDetected` → **FAILURE** → Sequence ObstacleAvoidance falla
4. `NavigateToWaypoint` → **SUCCESS**
5. Resultado: **NAVEGAR A WAYPOINT**

### Caso 3: Batería baja (prioridad máxima)
1. `Fallback` evalúa `LowBatteryRecovery`
2. `IsBatteryLow` → **SUCCESS**
3. `ReturnToBase` → **SUCCESS**
4. `Fallback` devuelve SUCCESS → rama 2 no se evalúa
5. Resultado: **VOLVER A BASE**

## Visualización en Groot

El árbol fue monitoreado en tiempo real mediante `PublisherZMQ` conectado a Groot
(Publisher Port: 1666, Server Port: 1667). Se observaron los tres casos anteriores
con los nodos cambiando de color según su estado (verde=SUCCESS, rojo=FAILURE, gris=no evaluado).
