# Importar datos

Para traer a tu cuenta los datos que tenías en la versión anterior de BodyLens.

## Desde «Tu cuenta» → Importar datos
- **Ficheros que acepta**:
  - **`snap.json`**: la copia de todos los datos que llevaba la página anterior (puede incluir varios perfiles).
  - **Copia completa (JSON)**: la que se descarga en Ajustes → Datos y copias → **Descargar copia completa**.
- **¿Qué datos de la copia son tuyos?**: si la copia trae varios perfiles, elige el tuyo. Cada persona importa su perfil desde su propia cuenta con el mismo fichero.
- **Traer también los demás perfiles**: opcional, los añade como perfiles dentro de tu cuenta.
- **Qué hace**: sustituye en tu cuenta los documentos que vengan en la copia (ajustes, pesadas, medidas, actividad, sueño, comidas…). Los registros de Salud (`hklog`, avisos) se **suman** sin duplicar.

## Desde Ajustes → Datos y copias → Importar una copia…
- Solo acepta la **Copia completa (JSON)** de la propia app. Si eliges un `snap.json`, la app te indica que lo importes en «Tu cuenta».

## Por consola (administración)
```
docker exec bodylens python -m app.data.importer /data/import/snap.json --usuario <usuario> [--perfil <id>] [--con-perfiles]
```
