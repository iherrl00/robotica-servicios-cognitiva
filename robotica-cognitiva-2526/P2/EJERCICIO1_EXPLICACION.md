# Ejercicio 1 - Comprensión de Behavior Trees

## Diferencias entre FSM y Behavior Trees

### Máquinas de Estados Finitas (FSM)

Una FSM modela el comportamiento mediante un conjunto finito de **estados** y **transiciones** entre ellos. En cada momento el sistema está en exactamente un estado, y pasa de uno a otro cuando se cumple una condición de transición.

**Características:**
- El comportamiento depende del estado actual y del evento que ocurre.
- Las transiciones se definen explícitamente entre pares de estados.
- Son fáciles de entender para comportamientos simples.
- **Problema de escalabilidad:** al añadir nuevos estados, el número de transiciones crece de forma cuadrática, haciendo el sistema difícil de mantener (*state explosion problem*).
- El comportamiento está fuertemente acoplado: cada estado conoce a qué estados puede ir.

### Behavior Trees (BT)

Un BT modela el comportamiento como un árbol jerárquico que se recorre (se "tickea") de forma periódica desde la raíz. Cada nodo devuelve uno de tres estados: **SUCCESS**, **FAILURE** o **RUNNING**.

**Características:**
- **Modularidad:** cada subárbol encapsula un comportamiento independiente y reutilizable.
- **Escalabilidad:** añadir nuevos comportamientos no requiere redefinir transiciones globales.
- **Separación clara** entre decisiones (nodos de control) y acciones (nodos hoja).
- **Reactividad:** el árbol se re-evalúa en cada tick, permitiendo responder a cambios del entorno.
- La lógica de control fluye de arriba hacia abajo, de forma predecible.

| Característica        | FSM                        | Behavior Tree               |
|-----------------------|----------------------------|-----------------------------|
| Escalabilidad         | Baja (state explosion)     | Alta (estructura jerárquica)|
| Modularidad           | Baja                       | Alta                        |
| Reutilización         | Difícil                    | Fácil                       |
| Legibilidad           | Buena para casos simples   | Buena para casos complejos  |
| Transiciones          | Explícitas entre estados   | Implícitas por jerarquía    |

---

## Funcionamiento de los nodos

### Sequence (→)

Ejecuta sus hijos **en orden** de izquierda a derecha.
- Si un hijo devuelve **FAILURE** → el Sequence devuelve **FAILURE** y para.
- Si un hijo devuelve **SUCCESS** → pasa al siguiente hijo.
- Si **todos** los hijos devuelven SUCCESS → el Sequence devuelve **SUCCESS**.
- Equivale a un **AND lógico**: todos deben tener éxito.

**Ejemplo:** *Si puedo ver al objetivo AND puedo alcanzarlo → atacar*

### Fallback / Selector (?)

Ejecuta sus hijos **en orden** de izquierda a derecha buscando uno que tenga éxito.
- Si un hijo devuelve **SUCCESS** → el Fallback devuelve **SUCCESS** y para.
- Si un hijo devuelve **FAILURE** → pasa al siguiente hijo.
- Si **todos** los hijos devuelven FAILURE → el Fallback devuelve **FAILURE**.
- Equivale a un **OR lógico**: basta con que uno tenga éxito.

**Ejemplo:** *Intentar abrir puerta con llave OR forzar la puerta OR buscar otra ruta*

### Condition

Nodo hoja que **evalúa una condición** del entorno o del robot.
- Devuelve **SUCCESS** si la condición se cumple.
- Devuelve **FAILURE** si la condición no se cumple.
- No ejecuta acciones, solo consulta el estado.
- Es instantáneo (no tiene estado RUNNING).

**Ejemplo:** `¿Hay obstáculo?`, `¿Batería baja?`, `¿Se ha llegado al destino?`

### Action

Nodo hoja que **ejecuta una acción** en el robot o entorno.
- Devuelve **RUNNING** mientras la acción está en curso.
- Devuelve **SUCCESS** cuando la acción se completa con éxito.
- Devuelve **FAILURE** si la acción falla o no puede ejecutarse.

**Ejemplo:** `Avanzar`, `Girar`, `Detenerse`, `Navegar a waypoint`
