# Ejercicio 2: Extensión del ejemplo básico

## Modificación realizada
Se añadió un nuevo estado `BazState` que se ejecuta entre BAR y FOO.

## Código del nuevo estado
```python
class BazState(State):
    def __init__(self) -> None:
        super().__init__(outcomes=["outcome_par", "outcome_impar"])

    def execute(self, blackboard: Blackboard) -> str:
        yasmin.YASMIN_LOG_INFO("Executing state BAZ")
        time.sleep(2)
        
        counter_str = blackboard["foo_str"]
        counter_value = int(counter_str.split(": ")[1])
        
        if counter_value % 2 == 0:
            yasmin.YASMIN_LOG_INFO(f"Contador {counter_value} es PAR")
            return "outcome_par"
        else:
            yasmin.YASMIN_LOG_INFO(f"Contador {counter_value} es IMPAR")
            return "outcome_impar"
```

## Cambios en las transiciones
```python
sm.add_state("BAR", BarState(), transitions={"outcome3": "BAZ"})  # Antes iba a FOO
sm.add_state("BAZ", BazState(), transitions={
    "outcome_par": "FOO",    # Ambos outcomes van a FOO
    "outcome_impar": "FOO"
})
```

## Cómo afecta al comportamiento del sistema

### Flujo original (Ejercicio 1):
FOO → BAR → FOO → BAR → FOO → ... → outcome4

### Nuevo flujo (Ejercicio 2):
FOO → BAR → **BAZ** → FOO → BAR → **BAZ** → FOO → ... → outcome4

### Cambios específicos:

1. **Tiempo de ejecución**: Cada ciclo ahora tarda 2 segundos más (BAZ ejecuta durante 2s)

2. **Lógica adicional**: Se añade validación de paridad del contador
   - Contador 1 → IMPAR
   - Contador 2 → PAR
   - Contador 3 → IMPAR

3. **Ramificación sin efecto práctico**: Aunque BAZ tiene dos outcomes diferentes, ambos conducen al mismo destino (FOO). Esto muestra la flexibilidad del sistema para futuras modificaciones.

4. **Lectura del Blackboard**: BAZ lee y procesa datos del Blackboard sin modificarlos, demostrando el uso de datos compartidos entre estados.

## Ventajas de esta arquitectura
- Fácil añadir estados intermedios sin modificar los estados existentes
- Las transiciones se reconfiguran fácilmente
- Los estados están desacoplados (BAZ no necesita conocer FOO o BAR)
