# Sueño

Sirve para ver cómo duermes: la última noche, tu saldo de sueño, la evolución, el horario y los análisis. Incluye siestas, fases del sueño y cruces con tu peso.

## Origen de los datos y reglas de las noches

- El sueño llega principalmente de **Apple Salud** (a través de Health Auto Export): las noches de AutoSleep o del Apple Watch y las siestas. **Withings** rellena las noches que Salud no tenga.
- **Ventana de la noche**: la noche de un día es la que termina entre las 17:00 de la víspera y las 17:00 de ese día. Debe acabar después de las 03:00; lo que acabe antes se trata como siesta. Cada noche se asocia al día en que te levantas.
- **Episodios**: dos ratos de sueño separados por más de 90 minutos son episodios distintos. Dos episodios nocturnos separados por 4 horas o menos se unen y el hueco cuenta como desvelo.
- **Desvelos**: huecos de al menos 10 minutos dentro de la noche.
- **Fuente de la noche**: horario, tiempo dormido y desvelos de AutoSleep si lo hay; si no, del Apple Watch; si no, de la fuente con más sueño. Si el Watch registra claramente más sueño que AutoSleep, manda el Watch. Las fases (profundo y REM) salen del Watch.
- **Siestas**: episodios de al menos 10 minutos fuera de la noche. En la tarjeta de siestas, el día va de las 20:00 de la víspera a las 20:00.
- Si Salud reenvía una noche (por ejemplo, AutoSleep la rehace al despertarte), la última versión sustituye a la anterior.

## Pestañas

- **Noche**, **Saldo**, **Evolución**, **Horario** y **Análisis**. La app recuerda la última abierta.

## Periodo

- El selector flotante (1 sem a Todo) se comparte con las demás secciones. Con **1 sem** se navega semana a semana con flechas; con periodos más largos, las noches se muestran como barras o calendario.

## Noche

- **Última noche** (o la elegida en la tira de la semana, o en las barras o el calendario del periodo): tiempo dormido en grande, eficiencia (porcentaje del tiempo en cama que duermes) y tiempo en cama.
- Interruptor **Ver**: colorea las noches por **Calificación** (por defecto) o por **Horas**.
- **Reloj del sueño**: arco con la hora de acostarte y levantarte, tu horario habitual en discontinua y los desvelos. Tocarlo lo amplía.
- **Calificación** (0 a 100): suma de cuatro partes.
  - 50 puntos por duración frente a tu objetivo de horas.
  - 20 por eficiencia (0 si es 70 % o menos, completo con 95 %).
  - 15 por sueño profundo (completo con un 15 % o más del tiempo dormido).
  - 15 por regularidad de la hora de acostarte frente a tu mediana de los últimos 90 días (sin penalización hasta 45 minutos de diferencia).
  - Color: verde desde 75, ámbar desde 50, rojo por debajo. Con el modo Horas: verde si llegas al objetivo, ámbar si te falta menos de 1 hora, rojo si más.
- **Fases**: barra y leyenda con Profundo, Ligero, REM y Despierto de la noche.
- **Datos nocturnos de Apple Salud** (si llegaron): SpO2 nocturna con su mínima, VFC nocturna y frecuencia respiratoria.
- **Cifras de la noche**: pulso durmiendo (con su mínimo), despertares y tiempo despierto, y tu hora de acostarte y de levantarte frente al objetivo de Ajustes (con cuántos minutos antes o más tarde).
- **Saldo de sueño**: enlace al apartado Saldo con tu saldo actual.
- **Nota del día**: caja para añadir un comentario (hasta 300 caracteres).
- **Siestas**: lista de siestas del día con hora, duración y pulso, y una tira que las sitúa junto a la noche. Las siestas suman al saldo de sueño.
- **Bienestar de la última noche**: indicadores tipo reloj de la noche (tiempo dormido, preparación, pulso durmiendo, consistencia, eficiencia, sueño profundo, despertares y hora recomendada para acostarte esta noche). Se calculan con tus últimas semanas y necesitan al menos 3 noches.
  - **Preparación** (0 a 100): 45 % calificación de la noche, 30 % saldo de la última semana y 25 % pulso durmiendo frente a tus últimas noches. Etiquetas: Bajo, Regular, Bueno, Excelente.

## Saldo

- **Saldo de sueño**: lo que has dormido en las últimas 7 noches, más las siestas, frente a tu objetivo por noche. Las noches sin datos no cuentan (ni su objetivo). Positivo es superávit; negativo, deuda. El anillo muestra el porcentaje y el texto indica cuánto has dormido de cuánto necesitabas. Muestra además planes de 7 y 14 noches para saldar la deuda.
- **Evolución del saldo**: cada punto es el saldo de las 7 noches anteriores; las franjas y los puntos rojos son fines de semana.
- **Noche a noche**: lo que suma o resta cada noche (siestas incluidas). En las noches sin datos aparece **Añadir**: puedes apuntar a mano la hora a la que te acostaste y te levantaste (la noche debe durar entre 30 minutos y 20 horas). Si luego llega la noche real de Withings o de Apple Salud, la sustituye. Las noches apuntadas a mano se pueden editar o borrar.
- **En cifras**: media dormida, noches en el objetivo, racha actual, días con deuda, peor saldo y siestas aportadas.
- **Qué noches te endeudan**: saldo medio por día de la semana.
- **Cómo te afecta la deuda**: compara tus días con mucha deuda con los días al día en VFC, pulso en reposo, pasos, nota de comidas y calificación (necesita al menos 5 días de cada tipo).
- **Plan para saldar la deuda**: si hay deuda, una tabla con cuánto dormir cada noche y a qué hora acostarte para saldarla en 3, 5, 7, 10 o 14 noches. Usa tu eficiencia media del último mes.
- Tocar la tarjeta del saldo abre el informe, con la hora objetivo de acostarte y despertarte.

## Evolución

- **Histórico**: pestañas **Calificación**, **Calidad** (profundo más REM), **Sueño** (horas), **Profundo**, **Al acostarte** y **Pulso**. Muestra barras del periodo y un calendario de hasta 18 semanas; tocar un día lo selecciona.
- **Cifras del periodo**: tiempo dormido, tiempo en cama y eficiencia, hora mediana a la que te duermes y a la que te levantas, regularidad de la hora de dormirte, noches que llegan al objetivo y reparto de profundo, REM y ligero.
- **Horas de sueño** por noche con la línea de objetivo.
- **Lo que dice tu sueño**: frases con tus propios datos.
- **Tendencia**: mediana mensual de lo que duermes y su media de 3 meses, con todo tu historial.
- **A qué hora duermes**: hora mediana mensual a la que te duermes y a la que te levantas.

## Horario

- **Horario**: desde que te duermes hasta que te despiertas, noche a noche. En verde, lo dormido hasta tu hora objetivo de levantarte; en rojo, lo dormido después (el fin de semana se mide con su propio horario). Líneas discontinuas: tu hora habitual; continuas: la media móvil.
- **Fases del sueño**: horas de cada fase por noche (Apple Watch).
- **Por noche de la semana**: horas dormidas de media según el día en que te acuestas.

## Análisis

- **Calendario de sueño**: horas de las últimas 16 semanas, más intenso cuanto más duermes.
- **Cuánto duermes**: reparto de las noches del periodo por horas dormidas.
- **Entre semana y fin de semana**: noches de domingo a jueves frente a viernes y sábado.
- **Calidad: sueño profundo y REM**: parte de cada semana en profundo y en REM.
- **Sueño y peso**: cuánto pesas por la mañana frente a los días de alrededor, según lo que dormiste esa noche (con todo tu historial).

## Objetivos

El objetivo de horas por noche (por defecto 7 h, entre 4 y 12) y el horario objetivo para acostarte y despertarte (laborables y fin de semana; por defecto 00:00 y 07:00) se cambian en Ajustes → Objetivos y plan.
