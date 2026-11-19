# Cuentas y acceso

Cada persona tiene su propia cuenta en BodyLens, con sus datos separados de los de las demás. Solo se entra con usuario y contraseña.

## Entrar
- **Pantalla de entrar** (`/login`): usuario y contraseña. Si fallas varias veces seguidas, hay que esperar unos minutos.
- **Sesión**: dura 90 días en ese navegador. Para salir, «Tu cuenta» → **Cerrar sesión** (también borra los datos guardados en ese navegador).
- **Cuenta pendiente**: si tu petición aún no está aprobada, al entrar se avisa de que te llegará un correo cuando lo esté.
- **Cuenta inicial de un despliegue nuevo**: mientras la cuenta `admin` conserve su contraseña por defecto (`admin123`), la pantalla de entrar la muestra con un botón **Usar**. Desaparece al cambiarla.

## Pedir una cuenta
- En la pantalla de entrar, **¿No tienes cuenta? Pide una**.
- **Datos que se piden**: usuario (minúsculas, números, punto, guion), nombre y apellidos, un correo válido (no puede estar ya en otra cuenta), contraseña (al menos 4 caracteres) y un mensaje opcional.
- **Qué pasa después**: la cuenta queda pendiente; la administración recibe un correo y la aprueba o la rechaza. A ti te llega un correo al pedirla y otro cuando se decide.

## Registro con invitación
- Un enlace `/registro?c=…` que crea la administración. Vale para **una** cuenta y caduca a los pocos días.
- Se piden los mismos datos que en la petición, pero la cuenta queda activa al momento.

## Primera entrada con contraseña provisional
- Si tu cuenta se creó con una contraseña provisional, al entrar se pide **tu propia contraseña** y puedes cambiar el usuario y el nombre. Hasta entonces no se abre la app.

## Tu cuenta (`/cuenta`)
Se abre desde el menú del perfil (arriba a la izquierda) → **Tu cuenta**.
- **Nombre y apellidos** y **correo**: el correo recibe todos los avisos.
- **Contraseña**: pide la actual; al cambiarla se cierran las sesiones de los demás dispositivos.
- **Pareja** y **Sincronización**: ver [pareja](pareja.md) y [sincronización](sincronizacion.md). Importar copias está en Ajustes → Datos y copias ([importar](importar.md)).
- **Administración**: solo para cuentas administradoras; ver [administración](administracion.md).

## Privacidad
- Tus datos solo los ves tú. Lo de **Ciclo** e **intimidad** lo ve también tu pareja si habéis unido las cuentas.
- Las contraseñas se guardan cifradas (argon2); nadie puede leerlas.
