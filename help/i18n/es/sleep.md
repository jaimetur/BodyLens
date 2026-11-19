<!-- en: 9deb6c2fd63c6ae7 -->
# Sueño

Sirve para ver cómo duermes: la última noche, tu saldo de sueño, la evolución, el horario y el análisis. Incluye siestas, fases del sueño y comparaciones con tu peso.

## Origen de los datos y reglas de las noches

- El sueño viene sobre todo de **Apple Salud** (iPhone, a través de Health Auto Export) o de **Android** (Health Connect, a través de la app de BodyLens): noches de AutoSleep o del Apple Watch (iPhone) o de tu app de salud de Android, y siestas. **Withings** rellena las noches que Salud no tiene.
- **Ventana de la noche**: la noche de un día es la que termina entre las 17:00 del día anterior y las 17:00 de ese día. Debe terminar después de las 03:00; lo que termine antes se trata como siesta. Cada noche se asigna al día en que te despiertas.
- **Episodios**: dos tramos de sueño separados por más de 90 minutos son episodios distintos. Dos episodios de noche separados por 4 horas o menos se juntan y el hueco cuenta como un desvelo.
- **Desvelos**: huecos de al menos 10 minutos dentro de la noche.
- **Origen de la noche**: horario, tiempo dormido y desvelos de AutoSleep si lo hay; si no, del Apple Watch; si no, de la fuente con más sueño. Si el reloj registra claramente más sueño que AutoSleep, prevalece el reloj. Las fases (profundo y REM) vienen del reloj.
- **Siestas**: episodios de al menos 10 minutos fuera de la noche. En la tarjeta de siestas, el día va de las 20:00 del día anterior a las 20:00.
- Si Salud reenvía una noche (por ejemplo, AutoSleep la rehace al despertarte), la última versión sustituye a la anterior.

## Pestañas

- **Noche**, **Saldo**, **Evolución**, **Horario** y **Análisis**. La app recuerda la última que abriste.

## Periodo

- El selector flotante (de 1 sem a Todo) se comparte con las otras secciones. Con **1 sem** navegas semana a semana con flechas; con periodos más largos, las noches se muestran como barras o un calendario.

## Noche

- **Anoche** (o la elegida en la tira de la semana, o en las barras o el calendario del periodo): tiempo dormido en grande, eficiencia (porcentaje del tiempo en la cama que duermes) y tiempo en la cama.
- Interruptor de **vista**: colorea las noches por **Nota** (por defecto) o por **Horas**.
- **Reloj de sueño**: arco con tu hora de acostarte y de levantarte, tu horario habitual discontinuo y los desvelos. Al tocarlo se agranda.
- **Nota** (0 a 100): suma de cuatro partes.
  - 50 puntos por la duración frente a tu objetivo de horas.
  - 20 por la eficiencia (0 si es del 70 % o menos, completo con el 95 %).
  - 15 por el sueño profundo (completo con un 15 % o más del tiempo dormido).
  - 15 por la regularidad de tu hora de acostarte frente a tu mediana de los últimos 90 días (sin penalización hasta 45 minutos de diferencia).
  - Color: verde desde 75, ámbar desde 50, rojo por debajo. En modo Horas: verde si llegas al objetivo, ámbar si te faltan menos de 1 hora, rojo si más.
- **Fases**: barra y leyenda con Profundo, Ligero, REM y Despierto de la noche.
- **Datos nocturnos de Apple Salud / Android** (si llegaron): SpO2 nocturna con su mínimo, HRV nocturna y frecuencia respiratoria.
- **Cifras de la noche**: pulso dormido (con su mínimo), despertares y tiempo despierto, y tu hora de acostarte y de levantarte frente al objetivo de Objetivos, plan y comidas (con cuántos minutos antes o después).
- **Saldo de sueño**: enlace a la sección Saldo con tu saldo actual.
- **Nota del día**: cuadro para añadir un comentario (hasta 300 caracteres).
- **Siestas**: lista de las siestas del día con hora, duración y frecuencia cardiaca, y una tira que las sitúa junto a la noche. Las siestas suman al saldo de sueño.
- **Bienestar de anoche**: indicadores tipo medidor de la noche (tiempo dormido, preparación, pulso dormido, consistencia, eficiencia, sueño profundo, despertares y hora de acostarte recomendada para esta noche). Se calculan con tus últimas semanas y necesitan al menos 3 noches.
  - **Preparación** (0 a 100): 45 % nota de la noche, 30 % saldo de la última semana y 25 % pulso dormido frente a tus últimas noches. Etiquetas: Baja, Regular, Buena, Excelente.

## Saldo

- **Saldo de sueño**: lo que has dormido en las últimas 7 noches, más las siestas, frente a tu objetivo por noche. Las noches sin datos no cuentan (ni su objetivo). Positivo es un excedente; negativo, una deuda. El anillo muestra el porcentaje y el texto dice cuánto has dormido de cuánto necesitabas. También muestra planes de 7 y 14 noches para pagar la deuda.
- **Evolución del saldo**: cada punto es el saldo de las 7 noches anteriores; las bandas y los puntos rojos son los fines de semana.
- **Noche a noche**: lo que suma o resta cada noche (siestas incluidas). En las noches sin datos aparece **Añadir**: puedes apuntar a mano la hora a la que te acostaste y te levantaste (la noche debe durar entre 30 minutos y 20 horas). Si la noche real de Withings o Apple Salud llega después, la sustituye. Las noches apuntadas a mano se pueden editar o borrar.
- **En cifras**: media dormida, noches en el objetivo, racha actual, días en deuda, peor saldo y siestas aportadas.
- **Qué noches te meten en deuda**: saldo medio por día de la semana.
- **Cómo te afecta la deuda**: compara tus días con mucha deuda con los días en que estás al día en HRV, frecuencia cardiaca en reposo, pasos, nota de comidas y nota (necesita al menos 5 días de cada tipo).
- **Plan para pagar la deuda**: si hay deuda, una tabla con cuánto dormir cada noche y a qué hora acostarte para pagarla en 3, 5, 7, 10 o 14 noches. Usa tu eficiencia media del último mes.
- Al tocar la tarjeta del saldo se abre el informe, con la hora objetivo de acostarte y de levantarte.

## Evolución

- **Histórico**: pestañas **Nota**, **Calidad** (profundo más REM), **Sueño** (horas), **Profundo**, **Cuándo te acuestas** y **Frecuencia cardiaca**. Muestra barras del periodo y un calendario de hasta 18 semanas; al tocar un día se selecciona.
- **Cifras del periodo**: tiempo dormido, tiempo en la cama y eficiencia, mediana de la hora a la que te duermes y te despiertas, regularidad de tu hora de acostarte, noches que llegan al objetivo y desglose de profundo, REM y ligero.
- **Horas de sueño** por noche con la línea del objetivo.
- **Lo que dice tu sueño**: frases con tus propios datos.
- **Tendencia**: mediana mensual de cuánto duermes y su media de 3 meses, con todo tu historial.
- **A qué hora duermes**: mediana mensual de la hora a la que te duermes y te despiertas.

## Horario

- **Horario**: desde que te duermes hasta que te despiertas, noche a noche. En verde, lo que dormiste hasta tu hora objetivo de levantarte; en rojo, lo que dormiste después (el fin de semana se mide con su propio horario). Líneas discontinuas: tu hora habitual; líneas continuas: la media móvil.
- **Fases del sueño**: horas de cada fase por noche (Apple Watch).
- **Por noche de la semana**: media de horas dormidas según el día en que te acuestas.

## Análisis

- **Calendario de sueño**: horas de las últimas 16 semanas, más intenso cuanto más duermes.
- **Cuánto duermes**: desglose de las noches del periodo por horas dormidas.
- **Entre semana y fines de semana**: noches de domingo a jueves comparadas con las de viernes y sábado.
- **Calidad: sueño profundo y REM**: parte de cada semana en profundo y en REM.
- **Sueño y peso**: cuánto pesas por la mañana frente a los días de alrededor, según cómo dormiste esa noche (con todo tu historial).

## Objetivos

El objetivo de horas por noche (7 h por defecto, entre 4 y 12) y el horario objetivo para acostarte y levantarte (entre semana y fines de semana; 00:00 y 07:00 por defecto) se cambian en Objetivos, plan y comidas → Objetivos y plan.
