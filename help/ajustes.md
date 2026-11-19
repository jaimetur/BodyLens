# Ajustes

Sirve para configurar la app: perfiles y PIN, datos personales, objetivos y plan de pérdida, fórmula de Comidas, copias de seguridad y exportación a PDF.

## Cómo se abre

- En el ordenador, en la barra lateral: **Ajustes** (ajustes generales) y **Gestionar perfiles** (parte de perfiles).
- En el móvil, con el icono de ajustes de la barra superior. Desde el botón de perfil también se llega a ambas.
- El botón **✕** de la barra superior cierra Ajustes y te devuelve a la sección y al punto de la página en que estabas.

## Pestañas

Ajustes tiene dos grupos de pestañas. Se recuerda la última abierta de cada grupo.

- **Perfiles**: Perfiles y Datos personales.
- **Ajustes generales**: Objetivos y plan, Comidas y Datos y copias.

---

## Perfiles

- Cada persona tiene sus propios datos. Se cambia de perfil con el botón de perfil (iniciales y nombre) junto al título de la barra superior, que también ofrece **Gestionar perfiles**, **Ajustes** y **Bloquear perfil** (si el perfil tiene PIN).
- Cada fila de perfil permite:
  - **Nombre** y **color** (el color y las iniciales identifican el perfil).
  - **Ciclo**: marca qué perfil recibe los datos del ciclo menstrual que llegan de Apple Salud. Solo uno puede estar marcado.
  - **Pareja**: vincula dos perfiles entre sí. Al vincularlos aparece «desde» para indicar la fecha de inicio de la relación; la actividad sexual de la pareja anterior a esa fecha no se cuenta.
  - **Poner PIN** / **Cambiar PIN** / **Quitar PIN**: PIN de 4 cifras para el perfil.
  - **PIN privado**: PIN de 4 cifras para Ciclo e intimidad (ver más abajo).
  - **Borrar** (pide confirmación con «¿Seguro?»): quita el perfil de la lista. Sus datos siguen guardados por si lo vuelves a crear con el mismo nombre. El perfil principal no se puede borrar.
- **Añadir perfil**: escribe un nombre y pulsa **Añadir perfil**. Cámbiate a él con el botón de perfil.

### PIN del perfil
- Es un bloqueo de pantalla de 4 cifras con teclado numérico. **No cifra los datos.**
- Al abrir la app o cambiar a un perfil con PIN, se pide. Tras 5 intentos fallidos hay que esperar 30 segundos.
- La pantalla de bloqueo permite **Entrar con otro perfil**.
- **Bloquear perfil** (en el menú de perfil) vuelve a pedir el PIN.
- Entrar con el **PIN normal** abre el perfil sin Ciclo e intimidad; entrar con el **PIN privado** abre todo.

### PIN privado
- Protege la sección Ciclo e intimidad. Mientras no lo cambies, es **0000**.
- Para cambiarlo hay que escribir el PIN privado actual y uno nuevo de 4 cifras distinto de 0000. **Volver a 0000** lo restablece.
- Si el perfil tiene PIN normal y PIN privado propio, al entrar con el PIN normal la sección Ciclo e intimidad ni aparece.

### Datos personales
- **Altura (cm)**: entre 120 y 230. Se usa para el IMC, el índice de masa magra, las zonas de referencia y las fórmulas de las medidas con cinta.
- **Sexo para las fórmulas**: Sin indicar, Hombre o Mujer. Se usa para las zonas de grasa, el índice de masa magra, el VO2 máx y las fórmulas de las medidas con cinta.
- **Fecha de nacimiento**: afina los rangos de grasa y del VO2 máx a tu franja de edad.
- Pulsa **Guardar perfil**.

---

## Objetivos y plan

### Objetivos diarios
Marcan las líneas de objetivo de las barras y cuentan los días y noches que los cumples (Actividad y Sueño).

- **Pasos al día** (1.000 a 50.000; por defecto 8.000).
- **Minutos de ejercicio al día** (5 a 300; por defecto 30).
- **Calorías activas al día** (50 a 3.000 kcal; por defecto 400).
- **Sueño por noche** en horas (4 a 12; por defecto 7).
- **Horario objetivo**: hora de acostarte y de despertarte en laborables y en fines de semana (por defecto 00:00 y 07:00).
- **Guardar objetivos** guarda los cambios; **Valores por defecto** los restablece.

### Plan de pérdida
- **Peso inicial**, **Objetivo final** (menor que el inicial) e **Inicio del plan**.
- **Tres ritmos semanales** (kg por semana, mayores que cero): el plan baja cada semana ese peso mientras estés por encima de 1,35 veces el objetivo (primer ritmo), por encima de 1,2 veces (segundo) y por encima del objetivo (ritmo final). Por defecto, 1; 0,75 y 0,5 kg por semana.
- Con esto se dibuja la línea del plan, los hitos y la comparación de Resumen y Peso.
- **Guardar plan**. Lo que cambies aquí se mantiene aunque lleguen otros valores.

---

## Comidas

- **Comidas · tus platos**: todos los platos que has anotado, de más a menos usados.
  - Cambia el nombre de un plato, bórralo, júntalos en uno (seleccionando varios y pulsando **Juntar**) o añade platos nuevos para que salgan en las sugerencias. Hay un buscador.
- **Nota de comidas y pérdida estimada**: los pesos de la nota del día y de la pérdida estimada.
  - **Pesos** del desayuno, almuerzo, cena, agua y deporte.
  - **Penalización** de los pecados de comida y de bebida.
  - **Nota por defecto** de una comida sin puntuar (0 a 5; por defecto 3).
  - **Factor de la pérdida estimada** (mayor que 0 y hasta 5).
  - Casillas: un día normal mantiene el peso (modelo neutro); contar todos los días aunque no te peses (con tu última pesada); y contar los días sin comidas anotadas con la nota por defecto.
  - Fórmula: pérdida estimada del día = factor × (objetivo − peso) ÷ objetivo × nota del día.
  - Una vista previa muestra el reparto en % de cada concepto.
  - **Guardar fórmula**, **Valores por defecto** (modelo neutro) y **Modelo de la hoja** (los valores de la hoja de cálculo original).

---

## Datos y copias

### Apple Salud
- Explica cómo configurar la app **Health Auto Export** en el iPhone para enviar a la app el pulso en reposo, la VFC, la saturación de oxígeno, la frecuencia respiratoria, el VO2 máx, la temperatura de muñeca, los ECG y los avisos del Apple Watch. Los datos se ven en Cuerpo → Corazón y en Sueño.
- Resumen de los pasos: crear una automatización de tipo API REST con formato JSON, y elegir los datos (métricas de salud, ECG y notificaciones de frecuencia cardiaca) y la frecuencia de envío. Para el historial, usa la carga manual de Health Auto Export.

### Origen de los datos
- Cifras de control: **días guardados**, **última pesada** y cuándo se leyeron los datos por última vez.
- Las pesadas y la composición vienen de la báscula **Withings**; sueño, actividad y entrenos, principalmente de **Apple Salud**.

### Copia de seguridad
- **Descargar copia completa**: guarda un archivo JSON con todo (pesadas, composición, medidas, actividad, sueño, entrenamientos, comidas, datos de Salud y ajustes del perfil actual). Su nombre incluye la fecha.
- **Importar una copia…**: elige un archivo de copia. Se muestra un resumen (fecha de la copia y número de días de cada tipo) y dos opciones:
  - **Combinar con lo actual**: añade lo que falte y, si un día está en los dos sitios, se queda el de la copia.
  - **Reemplazar todo**: deja tus datos exactamente como en la copia. Pide una confirmación extra («Sí, reemplazar todo»).
  - También puedes **Cancelar**. Si el archivo no es una copia de esta app, se avisa.
- **Historial (CSV)** y **Medidas (CSV)**: exportan tu historial de peso y tus medidas con cinta en CSV para hojas de cálculo.

---

## Exportar a PDF

- Se abre con el icono **PDF** de la barra superior (en Ajustes propone exportar todo).
- Opciones:
  - **Periodo**: 1 sem, 1 mes, 3 meses, 6 meses, 1 año o Todo; arranca con el de la sección en que estás.
  - **Orientación**: Vertical o Apaisado.
  - **Qué exportar**: **Esta pestaña**, **Elegir** (una cuadrícula por módulos y apartados, con **Marcar todo** y **Quitar todo**) o **Todo**.
- Pulsa **Ver vista previa**: se generan páginas A4 con las gráficas como las ves en la app, con el nombre del perfil y el periodo en la cabecera. Toca una página para ampliarla.
- **Descargar PDF** guarda el archivo; **Cambiar opciones** vuelve atrás.
- El PDF se hace siempre con el tema claro.
- La sección Ciclo e intimidad solo se puede exportar si has entrado con el PIN privado.
