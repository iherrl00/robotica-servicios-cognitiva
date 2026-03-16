# Ejercicio 10 - Exploración de las demos de py-trees

## Instalación

```bash
pip install py-trees
export PATH=$PATH:/home/user/.local/bin
```

## Ejecución de la demo

```bash
py-trees-demo-selector
```

## Salida observada

```
Tick 1: FFS → FAILURE | Running → RUNNING  → Selector: RUNNING
Tick 2: FFS → FAILURE | Running → RUNNING  → Selector: RUNNING
Tick 3: FFS → SUCCESS | Running → INVALID  → Selector: SUCCESS
```

## Árbol generado (--render)

El árbol tiene la siguiente estructura:

```
Selector (?)
├── FFS
└── Running
```

- **Selector** es el nodo raíz (hexágono cian en la imagen).
- **FFS** (Failure, Failure, Success) es el hijo de mayor prioridad.
- **Running** es el hijo de menor prioridad, ejecutándose continuamente.

## Respuestas a las preguntas

### ¿Qué tipo de nodo es el nodo raíz del árbol?
El nodo raíz es un **Selector** (equivalente al Fallback en BehaviorTree.CPP). Se representa con un hexágono y el símbolo `?`. Evalúa sus hijos de izquierda a derecha buscando uno que tenga éxito.

### ¿Qué comportamiento tiene un nodo Selector?
El Selector ejecuta sus hijos en orden de prioridad (izquierda a derecha):
- Si un hijo devuelve **SUCCESS** → el Selector devuelve SUCCESS y para.
- Si un hijo devuelve **FAILURE** → pasa al siguiente hijo.
- Si un hijo devuelve **RUNNING** → el Selector devuelve RUNNING y espera.
- Si todos fallan → el Selector devuelve **FAILURE**.

Equivale a un **OR lógico**: basta con que un hijo tenga éxito.

### ¿Qué sucede cuando una condición falla?
Cuando `FFS` devuelve FAILURE (ticks 1 y 2), el Selector no se detiene sino que pasa al siguiente hijo (`Running`). Esto permite implementar comportamientos de fallback: si la opción preferida no funciona, se prueba la siguiente. El hijo `Running` se mantiene activo (RUNNING) mientras el anterior sigue fallando.

### ¿Cómo cambia el flujo de ejecución del árbol en cada iteración?

- **Tick 1:** `FFS` falla (primera F de su secuencia) → el Selector activa `Running` → devuelve RUNNING.
- **Tick 2:** `FFS` vuelve a fallar (segunda F) → `Running` continúa → Selector sigue en RUNNING.
- **Tick 3:** `FFS` tiene éxito (la S de su secuencia) → el Selector interrumpe `Running` (pasa a INVALID) y devuelve SUCCESS. Esto demuestra la **interrupción por mayor prioridad**: cuando un hijo de mayor prioridad tiene éxito, cancela al hijo de menor prioridad que estaba en RUNNING.
