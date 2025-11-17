# quant

Библиотека симуляции квантовых вычислений.

## Пространства состояний

Системе из n кубитов соответствует пространство состояний C^{2^n}.

`quant_state(bits)` - подготавливаем состояние - элемент вычислительного базиса.

## Измерения

`quant_measure_observable(M)` - измерение наблюдаемой M
`quant_measure_comp(??)` - измерение в вычислительном базисе

Измерение происходит в конце, состояние после измерения не вычисляется.

## Квантовые схемы

`class Gate` - вентиль для квантовой схемы
* `gate_X(k)` - оператор Паули X, действующий на k-й кубит
* `gate_Y(k)` - --"-- Y
* `gate_Z(k)` - --"-- Z
и другие.
`quant_op_cz(k, l)` - контролируемый k-м кубитом Z для l-го кубита
`quant_op_cphase(k, l)` - контролируемый k-м кубитом phase для l-го кубита
`quant_op_toffoli(k, l, m)` - Toffoli gate

## Пример

```
state = quant_state([0] x 3)
u1 = quant_op_x(1)
u2 = quant_op_y(0)
u3 = quant_op_z(2)

scheme = u1 * u2 * u3
new_state = scheme * state
m = quant_measure_observable(M)

result = m(new_state)
```
