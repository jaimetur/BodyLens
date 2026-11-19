<!-- en: 85c19f384a697f4f -->
# Cuentas y acceso

Cada persona tiene su propia cuenta de BodyLens, con sus datos separados de los de los demás. Entras con tu nombre de usuario (o tu correo) y tu contraseña.

## Entrar
- **Pantalla de acceso** (`/login`): tu usuario o el correo de tu cuenta, y tu contraseña. Si fallas varias veces seguidas, tendrás que esperar unos minutos.
- **Sesión**: dura 90 días en ese navegador. Para salir, ve a «Tu cuenta» → **Cerrar sesión** (esto también borra los datos guardados en ese navegador).
- **Cuenta pendiente**: si tu petición aún no está aprobada, al entrar te avisa de que recibirás un correo cuando lo esté.
- **Cuenta inicial de un despliegue nuevo**: mientras la cuenta `admin` conserve su contraseña por defecto (`admin123`), la pantalla de acceso la muestra con un botón **Usar**. Desaparece en cuanto cambias la contraseña.

## Pedir una cuenta
- En la pantalla de acceso, **¿No tienes cuenta? Pídela**.
- **Datos que se piden**: usuario (minúsculas, números, punto y guion), nombre y apellidos, un correo válido (no puede pertenecer ya a otra cuenta), contraseña (al menos 4 caracteres) y un mensaje opcional.
- **Qué pasa después**: la cuenta queda pendiente; la administración recibe un correo y la aprueba o la rechaza. Recibes un correo al pedirla y otro cuando se decide.

## Registrarte con una invitación
- Es un enlace `/registro?c=…` creado por la administración. Sirve para **una** cuenta y caduca a los pocos días.
- Pide los mismos datos que la petición, pero la cuenta queda activa al momento.

## Primera entrada con una contraseña temporal
- Si tu cuenta se creó con una contraseña temporal, al entrar se te pide **tu propia contraseña** y puedes cambiar tu usuario y tu nombre. La app no se abre hasta que lo hagas.

## Tu cuenta (`/cuenta`)
Ábrela desde el menú del perfil (arriba a la izquierda) → **Tu cuenta**.
- **Nombre y apellidos** y **correo**: el correo recibe todas las notificaciones.
- **Idioma**: el idioma de toda la app y de los correos que recibes. Antes de entrar, elígelo con el selector 🌐 de la pantalla de acceso. Las cuentas nuevas empiezan en inglés (o en el idioma elegido al pedir la cuenta).
- **Contraseña**: pide la actual; al cambiarla se cierra tu sesión en los demás dispositivos.
- **Pareja** y **Sincronización**: mira [pareja](couples.md) y [sincronización](sync.md). Importar copias está en Ajustes → Datos y copias ([importar](import.md)).
- **Administración**: solo para cuentas de administrador; mira [administración](administration.md).

## Privacidad
- Solo tú puedes ver tus datos. Los datos del **ciclo** y de intimidad los ve también tu pareja si habéis unido vuestras cuentas.
- Las contraseñas se guardan cifradas (argon2); nadie puede leerlas.
