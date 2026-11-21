<!-- en: 21ad9894649e523d -->
# Comidas

Sirve para apuntar lo que comes cada día y puntuarlo, y para ver cuánto debería afectar a tu peso según una fórmula, comparado con lo que marca la báscula al día siguiente. Los pesos vienen de la báscula **Withings**; las comidas las escribes tú.

## Pestañas

- **Hoy**, **Registro** y **Análisis**. La app recuerda la última que abriste hasta que sale el bloqueo con PIN: entonces vuelve a empezar por la primera.
- En el móvil, la explicación de cada tarjeta con gráfico espera tras la **ⓘ** junto a su título (toca el título para verla u ocultarla).

## Periodo

- El selector flotante (de 1 sem a Todo) se comparte con las otras secciones y controla las cifras, las barras y las listas.

## Hoy

### Registro del día
- Elige el día en la tira de las últimas 4 semanas, de lunes a domingo (las flechas saltan 4 semanas), con el selector de fecha o con **Hoy**. Los días con apuntes tienen el color de su nota.
- **Desayuno**, **Almuerzo** y **Cena**: añade varios platos escribiendo y pulsando Intro. Se sugieren los platos que más has escrito. Los platos de una comida se pueden pasar a otra.
- **Pecados de comida** y **Pecados de bebida**: cada pecado tiene una cantidad. Cuentan automáticamente hasta un tope de −5.
- **Deporte** y **Nota**: texto libre.
- **Notas**: pulsa un valor para cada elemento; si lo vuelves a pulsar, se quita.
  - Desayuno, Almuerzo, Cena, Agua y Deporte: de 0 a 5.
  - Pecados de comida y de bebida: de −5 a 0. Se calculan automáticamente a partir de lo que has escrito; si pulsas un valor lo fijas a mano y, si lo vuelves a pulsar, vuelven a contar automáticamente.
- Junto al día se muestran, como contexto, el peso del día, los pasos, el sueño y los entrenamientos. Los cambios se guardan al instante.

### Pérdida estimada
- Anillo con la **nota del día** (en %), dividida en lo que suma (verde) y lo que resta (rojo).
- **Estimada y real**: la pérdida estimada por la fórmula para el día y, a su lado, el cambio real en la báscula entre la mañana de ese día y la del siguiente (solo si te pesas los dos días). Lo que comes un día se nota en la báscula a la mañana siguiente, por eso las tiras de semana se organizan por día de pesada.
- **Día perfecto**: lo que estimaría la fórmula con una nota del 100 %.
- **Tiras de semana**: una con la pérdida estimada y otra con la pérdida real, con flechas para moverte entre semanas y el botón **Hoy** para volver.
- **Cifras**: estimada y real de la semana, desde el inicio del plan, ritmo estimado de los últimos 14 días y la fecha en que llegarías al objetivo a ese ritmo.
- Con periodos de más de una semana, el panel resume el periodo y puedes navegar por periodos.

## Registro

- **Tu registro**: días apuntados, nota media, días con una nota del 70 % o más y días con pecados. Barras de la nota por día (línea de objetivo en el 70 %). Toca un día para verlo o cambiarlo.
- Tabla del periodo con día, peso, desayuno, almuerzo, cena, pecados, deporte, nota y pérdida estimada (también hay una versión en lista).
- **Lo que más repites**: los platos y pecados que más has apuntado en el periodo, por comida.

## Análisis

- **Pérdida estimada y real**: gráfico desde el inicio del plan con tres líneas: **Real**, **Estimada** y **Estimada sin pasar a la real** (la estimación acumulada no puede adelantarse a la real). Necesita tu plan (peso de partida, objetivo y fecha de inicio) y al menos dos pesadas. Debajo, la fórmula en uso y un enlace para ajustarla.
- **Lo que comes y tu peso**: mediana del cambio de peso del día siguiente según la nota del día (menos del 40 %, del 40 al 69 % y 70 % o más). Hacen falta al menos 8 días con nota y con peso al día siguiente.

## Cómo se calcula

- **Nota del día**: media ponderada de las notas. Las comidas sin nota cuentan como la nota por defecto (3, ajustable); el agua, el deporte y los pecados sin nota cuentan como 0. Los pecados restan con su propia penalización. El resultado se expresa como % del máximo posible, redondeado.
- **Pérdida estimada del día** = factor × (objetivo − peso) ÷ objetivo × nota del día. Con el modelo «neutro», un día normal (desayuno, almuerzo y cena con 3, sin agua, deporte ni pecados) mantiene tu peso: solo estima pérdida si lo haces mejor y ganancia si lo haces peor.
- Los pesos de la fórmula, las penalizaciones, el factor y varias opciones (contar los días sin pesada, contar los días sin comidas apuntadas, usar el modelo clásico) se cambian en Objetivos, plan y comidas → Comidas.
