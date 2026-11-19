# Importar datos

Para traer a tu cuenta una copia de BodyLens: la de la versión anterior o una que hayas descargado tú.

## Dónde
**Ajustes → Datos y copias → Importar una copia…** (es el único sitio).

## Qué ficheros acepta
- **Copia completa (JSON)**: la que se descarga en ese mismo apartado con **Descargar copia completa**.
- **`snap.json`**: la copia de todos los datos que llevaba la página anterior. Si trae varios perfiles, primero pregunta **de quién son los datos** que importas: cada persona importa los suyos desde su propia cuenta con el mismo fichero.

## Cómo se importa
- Antes de importar se ve un resumen de lo que trae la copia (pesadas, actividad, sueño, comidas, medidas…).
- **Combinar con lo actual**: añade lo que falte; si un día está en los dos sitios, se queda el de la copia.
- **Reemplazar todo**: deja tus datos exactamente como en la copia (pide confirmación).
- Lo importado se guarda en tu cuenta del servidor al momento.

## Por consola (administración)
```
docker exec bodylens python -m app.data.importer /data/import/snap.json --usuario <usuario> [--perfil <id>] [--con-perfiles]
```
