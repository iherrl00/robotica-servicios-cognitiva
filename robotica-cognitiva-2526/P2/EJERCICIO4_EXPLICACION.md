# Ejercicio 4 - Behavior Trees en Navegación (Nav2)

## Archivo localizado

El archivo equivalente a `navigate_w_replanning_and_recovery.xml` se encuentra en:

```
/opt/ros/humble/share/nav2_bt_navigator/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml
```

## XML del Behavior Tree

```xml
<!--
  This Behavior Tree replans the global path periodically at 1 Hz and it also has
  recovery actions specific to planning / control as well as general system issues.
-->
<root main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <RecoveryNode number_of_retries="6" name="NavigateRecovery">
      <PipelineSequence name="NavigateWithReplanning">
        <RateController hz="1.0">
          <RecoveryNode number_of_retries="1" name="ComputePathToPose">
            <ComputePathToPose goal="{goal}" path="{path}" planner_id="GridBased"/>
            <ClearEntireCostmap name="ClearGlobalCostmap-Context" service_name="global_costmap/clear_entirely_global_costmap"/>
          </RecoveryNode>
        </RateController>
        <RecoveryNode number_of_retries="1" name="FollowPath">
          <FollowPath path="{path}" controller_id="FollowPath"/>
          <ClearEntireCostmap name="ClearLocalCostmap-Context" service_name="local_costmap/clear_entirely_local_costmap"/>
        </RecoveryNode>
      </PipelineSequence>
      <ReactiveFallback name="RecoveryFallback">
        <GoalUpdated/>
        <RoundRobin name="RecoveryActions">
          <Sequence name="ClearingActions">
            <ClearEntireCostmap name="ClearLocalCostmap-Subtree" .../>
            <ClearEntireCostmap name="ClearGlobalCostmap-Subtree" .../>
          </Sequence>
          <Spin spin_dist="1.57"/>
          <Wait wait_duration="5"/>
          <BackUp backup_dist="0.30" backup_speed="0.05"/>
        </RoundRobin>
      </ReactiveFallback>
    </RecoveryNode>
  </BehaviorTree>
</root>
```

## Explicación de los nodos principales

### ComputePathToPose

Es un nodo **Action** que calcula una ruta global desde la posición actual del robot hasta el objetivo (`goal`). Utiliza un planificador global (en este caso `GridBased`, basado en Dijkstra/A*) y almacena el resultado en la variable de blackboard `{path}`.

- Devuelve **SUCCESS** si encuentra una ruta válida.
- Devuelve **FAILURE** si no puede calcular la ruta (objetivo inalcanzable, mapa no disponible, etc.).

Está envuelto en un `RecoveryNode`: si falla, intenta limpiar el costmap global (`ClearEntireCostmap`) antes de reintentar.

### FollowPath

Es un nodo **Action** que ejecuta la ruta calculada previamente y almacenada en `{path}`. Envía comandos de velocidad al robot mediante un controlador local (`FollowPath controller`).

- Devuelve **RUNNING** mientras el robot sigue la ruta.
- Devuelve **SUCCESS** cuando el robot llega al destino.
- Devuelve **FAILURE** si el controlador no puede seguir la ruta (obstáculo dinámico, robot bloqueado, etc.).

Al igual que `ComputePathToPose`, está envuelto en un `RecoveryNode` que limpia el costmap local si falla.

### RecoveryNode

Es un nodo de **control** que gestiona los fallos del sistema. Tiene dos hijos:
1. El comportamiento principal (navegar).
2. Las acciones de recuperación (limpiar costmaps, girar, esperar, retroceder).

Si el comportamiento principal falla, ejecuta las acciones de recuperación en `RoundRobin` (de forma rotativa). Tiene un máximo de `number_of_retries` intentos (6 en el nodo raíz). Si se agotan los reintentos, devuelve **FAILURE**.

## Flujo general del árbol

1. El `RecoveryNode` raíz intenta ejecutar `NavigateWithReplanning` hasta 6 veces.
2. Dentro, el `PipelineSequence` ejecuta en paralelo/secuencia:
   - Cada 1 Hz (`RateController`): recalcula la ruta con `ComputePathToPose`.
   - Continuamente: sigue la ruta con `FollowPath`.
3. Si algo falla, el `ReactiveFallback` activa las recuperaciones:
   - Si el objetivo cambió (`GoalUpdated`) → reinicia la navegación.
   - Si no → ejecuta acciones rotativas: limpiar costmaps → girar → esperar → retroceder.
