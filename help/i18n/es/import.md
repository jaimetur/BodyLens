<!-- en: c973035a97a24cd1 -->
# Importar datos

Para traer a tu cuenta una copia de BodyLens: una de la versión anterior o una que te hayas descargado tú.

## Dónde
**Ajustes → Datos y copias → Importar una copia…** (es el único sitio).

## Qué ficheros acepta
- **Copia completa (JSON)**: la que descargas en esa misma sección con **Descargar copia completa**.
- **`snap.json`**: la copia de todos los datos que guardaba la página anterior. Si contiene varios perfiles, primero se te pregunta **de quién son los datos** que importas: cada persona importa los suyos desde su cuenta con el mismo fichero.

## Cómo se importa
- Antes de importar ves un resumen de lo que contiene la copia (pesadas, actividad, sueño, comidas, medidas…).
- **Combinar con lo actual**: añade lo que falta; si un día está en los dos sitios, se queda la versión de la copia.
- **Reemplazar todo**: deja tus datos exactamente como en la copia (pide confirmación).
- Lo que importas se guarda enseguida en tu cuenta del servidor.

## Desde la consola (administración)
```
docker exec bodylens python -m app.data.importer /data/import/snap.json --usuario <usuario> [--perfil <id>] [--con-perfiles]
```
