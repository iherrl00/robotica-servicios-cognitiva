# Ejercicio 1: Análisis del ejemplo básico de YASMIN

## Código transcrito
El código está en `src/yasmin_practicas/yasmin_practicas/yasmin_demo_ejercicio1.py`

## Elementos principales y su función

### 1. **State (FooState, BarState)**
Son los estados individuales de la máquina de estados finitos. Cada estado:
- Hereda de la clase base `State`
- Define sus outcomes posibles en el constructor
- Implementa la lógica en el método `execute()`
- Retorna un outcome que determina la transición al siguiente estado

**FooState**: Ejecuta un contador que incrementa hasta 3, retornando "outcome1" para continuar o "outcome2" para finalizar.

**BarState**: Lee información del Blackboard y siempre retorna "outcome3" para volver a FOO.

### 2. **Blackboard**
Estructura de datos compartida entre todos los estados. Funciona como un diccionario Python donde:
- Los estados pueden escribir datos: `blackboard["foo_str"] = f"Counter: {self.counter}"`
- Otros estados pueden leerlos: `yasmin.YASMIN_LOG_INFO(blackboard["foo_str"])`
- Permite comunicación entre estados sin acoplamiento directo

### 3. **StateMachine**
La máquina de estados finitos que orquesta todo el comportamiento:
- Define los outcomes finales posibles del sistema completo
- Contiene y gestiona todos los estados
- Ejecuta las transiciones según los outcomes de cada estado
- Se ejecuta llamándola como función: `outcome = sm()`

### 4. **Transiciones**
Diccionario que mapea los outcomes de un estado al siguiente estado o al outcome final:
```python
transitions={
    "outcome1": "BAR",      # Si FOO retorna outcome1 -> va a BAR
    "outcome2": "outcome4", # Si FOO retorna outcome2 -> termina con outcome4
}
```

### 5. **YasminViewerPub**
Publica información de la FSM para visualización en tiempo real. Permite monitorizar gráficamente:
- Estados activos
- Transiciones ejecutadas
- Flujo del programa

## Flujo de ejecución observado
1. Inicia en estado FOO
2. FOO ejecuta, incrementa contador, guarda en Blackboard → outcome1
3. Transición a BAR
4. BAR ejecuta, lee del Blackboard → outcome3
5. Transición a FOO
6. Se repite 3 veces (contador < 3)
7. FOO retorna outcome2 → finaliza con outcome4
