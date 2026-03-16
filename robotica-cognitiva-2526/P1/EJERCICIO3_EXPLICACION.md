# Ejercicio 3: Concepto de Blackboard en YASMIN

## ¿Qué es un Blackboard?

Un **Blackboard** (pizarra) es una estructura de datos compartida que actúa como memoria global accesible por todos los estados de la máquina de estados finitos. En YASMIN, el Blackboard funciona como un diccionario Python donde los estados pueden leer y escribir información de forma dinámica.

## Propósito dentro de YASMIN

El Blackboard permite la **comunicación entre estados** sin necesidad de acoplamiento directo. Cada estado puede:
- **Escribir datos**: `blackboard["key"] = value`
- **Leer datos**: `value = blackboard["key"]`
- **Compartir contexto**: Pasar información de un estado a otro sin que estos se conozcan entre sí

### Ejemplo observado en los ejercicios:
```python
# En FooState (escritura)
blackboard["foo_str"] = f"Counter: {self.counter}"

# En BarState (lectura)
yasmin.YASMIN_LOG_INFO(blackboard["foo_str"])

# En BazState (lectura y procesamiento)
counter_str = blackboard["foo_str"]
counter_value = int(counter_str.split(": ")[1])
```

## Ventajas en arquitecturas cognitivas

### 1. **Desacoplamiento**
Los estados no necesitan conocerse entre sí. Solo interactúan con el Blackboard, facilitando:
- Añadir nuevos estados sin modificar los existentes
- Reutilizar estados en diferentes máquinas
- Mantener código modular y limpio

### 2. **Flexibilidad**
- No requiere definir estructuras de datos rígidas
- Permite añadir nuevas variables en tiempo de ejecución
- Facilita el prototipado rápido

### 3. **Simplicidad conceptual**
- Fácil de entender: es un diccionario compartido
- Debugging sencillo: se puede inspeccionar todo el estado global
- Intuitivo para desarrolladores

### 4. **Persistencia de contexto**
- Mantiene información a lo largo de toda la ejecución
- Permite que estados futuros accedan a datos de estados pasados
- Facilita implementar memoria a corto plazo del robot

## Desventajas en arquitecturas cognitivas

### 1. **Falta de control de tipos**
- No hay validación automática de tipos de datos
- Pueden ocurrir errores en tiempo de ejecución si un estado espera un tipo diferente
- Ejemplo: si un estado escribe un string y otro espera un int

### 2. **Acoplamiento implícito**
- Aunque los estados no se referencian directamente, están acoplados por las claves del Blackboard
- Si un estado cambia el nombre de una clave, puede romper otros estados
- No hay contrato explícito de qué datos debe contener el Blackboard

### 3. **Dificultad de debugging en sistemas complejos**
- En FSMs grandes, puede ser difícil rastrear qué estado modificó qué variable
- El Blackboard puede crecer descontroladamente con datos obsoletos
- No hay gestión automática de limpieza de datos

### 4. **Posibles condiciones de carrera**
- En sistemas concurrentes (múltiples FSMs), pueden surgir problemas de acceso simultáneo
- No hay mecanismos de bloqueo por defecto
- Requiere gestión manual de sincronización

### 5. **Escalabilidad limitada**
- Para arquitecturas muy complejas, un Blackboard global puede volverse caótico
- Dificulta la modularización en sistemas grandes
- No hay jerarquía ni namespaces para organizar datos

## Alternativas y mejoras posibles

1. **Blackboards jerárquicos**: Múltiples Blackboards con ámbitos diferentes
2. **Validación de esquemas**: Definir contratos de datos esperados
3. **Versionado de claves**: Evitar conflictos en nombres
4. **Gestión automática**: Limpiar datos cuando ya no se necesitan

## Conclusión

El Blackboard de YASMIN es una solución **pragmática y efectiva** para FSMs de complejidad baja-media. Sus ventajas en simplicidad y desacoplamiento lo hacen ideal para:
- Prototipos rápidos
- Robots con comportamientos reactivos
- Sistemas donde la flexibilidad es prioritaria

Sin embargo, para sistemas de misión crítica o muy complejos, puede requerir capas adicionales de validación y gestión de datos.
