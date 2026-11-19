# Sincronización

Los datos de la báscula (Withings) y de Apple Salud (Health Auto Export) llegan solos a tu cuenta.

## Cómo funciona ahora (fase 1)
- Cada **15 minutos** el servidor pide al Apps Script de tu hoja de Google que traiga lo último de Withings y rehaga las últimas noches, y después descarga la hoja.
- Si la hoja ha cambiado, la página abierta se **actualiza sola** (comprueba cada minuto y al volver a la pestaña).
- **Botón de la nube** (arriba): sincroniza al momento y muestra el resultado.
- El indicador de arriba dice si estás al día, si aún no hay datos o si algo ha fallado.

## Fuentes de tu cuenta
- La hoja de Google y el Apps Script de cada cuenta los configura la **administración** (ver [administración](administracion.md)). En «Tu cuenta» → **Datos** ves qué fuentes tienes, la última sincronización y su resultado, y puedes **Sincronizar ahora**.
- Sin fuentes configuradas, la app funciona con lo importado y lo que apuntes a mano.

## Próximamente (fase 2)
- Withings y Health Auto Export directos al servidor, cada cuenta con su autorización de Withings y su propia dirección de envío para Health Auto Export.
