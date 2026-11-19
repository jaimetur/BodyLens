# Comidas

Sirve para anotar lo que comes cada día y puntuarlo, y ver cuánto debería afectar a tu peso según una fórmula, frente a lo que marca la báscula al día siguiente. Los pesos los aporta la báscula **Withings**; las comidas las escribes tú.

## Pestañas

- **Hoy**, **Registro** y **Análisis**. La app recuerda la última abierta.

## Periodo

- El selector flotante (1 sem a Todo) se comparte con las demás secciones y controla las cifras, barras y listas.

## Hoy

### Pérdida estimada
- Anillo con la **nota del día** (en %), dividido en lo que suma (verde) y lo que resta (rojo).
- **Estimada y real**: la pérdida estimada por la fórmula para el día y, a su lado, el cambio real de la báscula entre la mañana de ese día y la del siguiente (solo si te pesas los dos días). Lo que comes un día se ve en la báscula a la mañana siguiente, por eso las tiras de la semana se organizan por día de pesada.
- **Día perfecto**: lo que estimaría la fórmula con una nota del 100 %.
- **Tiras de la semana**: una con la estimada y otra con la real, con flechas para moverte de semana y el botón **Hoy** para volver.
- **Cifras**: estimada y real de la semana, desde el inicio del plan, ritmo estimado de los últimos 14 días y fecha en que llegarías a la meta a ese ritmo.
- Con periodos de más de una semana, el panel resume el periodo y puedes navegar por periodos.

### Registro del día
- Elige el día con la tira de la semana (flechas para saltar de semana), con el selector de fecha o con **Hoy**. Los días anotados llevan el color de su nota.
- **Desayuno**, **Almuerzo** y **Cena**: añade varios platos escribiendo y pulsando Intro. Se sugieren los platos que más has escrito. Los platos de una comida se pueden mover a otra.
- **Pecados comida** y **Pecados bebida**: cada pecado tiene una cantidad. Cuentan solos hasta un tope de −5.
- **Deporte** y **Nota**: texto libre.
- **Puntuaciones**: pulsa un valor para cada concepto; volver a pulsarlo lo quita.
  - Desayuno, Almuerzo, Cena, Agua y Deporte: de 0 a 5.
  - Pecados de comida y de bebida: de −5 a 0. Se calculan solos a partir de lo anotado; si pulsas un valor lo fijas a mano y, si lo vuelves a pulsar, vuelven a contar solos.
- Junto al día se muestran, como contexto, el peso del día, los pasos, el sueño y los entrenos. Los cambios se guardan al momento.

## Registro

- **Tu registro**: días anotados, nota media, días con nota de 70 % o más y días con pecados. Barras de nota por día (línea de objetivo en 70 %). Toca un día para verlo o cambiarlo.
- Tabla del periodo con día, peso, desayuno, almuerzo, cena, pecados, deporte, nota y pérdida estimada (hay también una versión en lista).
- **Lo que más repites**: los platos y pecados que más veces has anotado en el periodo, por comida.

## Análisis

- **Pérdida estimada y real**: gráfica desde el inicio del plan con tres líneas: **Real**, **Estimada** y **Estimada sin pasar a la real** (la acumulada no se deja ir por delante de lo real). Necesita tu plan (peso inicial, objetivo y fecha de inicio) y al menos dos pesadas. Debajo, la fórmula en vigor y un enlace para ajustarla.
- **Lo que comes y tu peso**: mediana del cambio de peso al día siguiente según la nota del día (menos de 40 %, de 40 a 69 % y 70 % o más). Hacen falta al menos 8 días con nota y con peso al día siguiente.

## Cómo se calcula

- **Nota del día**: media ponderada de las puntuaciones. Las comidas sin puntuar valen la nota por defecto (3, ajustable); agua, deporte y pecados sin puntuar valen 0. Los pecados restan con su propia penalización. El resultado se expresa en % sobre el máximo posible, redondeado.
- **Pérdida estimada del día** = factor × (objetivo − peso) ÷ objetivo × nota del día. Con el modelo «neutro», un día normal (desayuno, almuerzo y cena a 3, sin agua, deporte ni pecados) mantiene el peso: solo estima pérdida si lo haces mejor y aumento si lo haces peor.
- Los pesos de la fórmula, las penalizaciones, el factor y varias opciones (contar días sin pesada, contar días sin comidas anotadas, usar el modelo de la hoja) se cambian en Ajustes → Comidas.
