"""Administración desde la línea de órdenes.

  python -m app.accounts.cli crear-admin USUARIO "Nombre"     # primera cuenta (pide la contraseña)
  python -m app.accounts.cli crear-usuario USUARIO "Nombre" [--correo X]   # cuenta con contraseña provisional
  python -m app.accounts.cli invitacion [nota]                # enlace de registro de un solo uso
  python -m app.accounts.cli contrasena USUARIO               # cambia la contraseña de una cuenta
  python -m app.accounts.cli usuarios                         # lista las cuentas
  python -m app.accounts.cli fuentes USUARIO [--hoja ID] [--apps-script URL]   # fase 1: hoja de Google de esa cuenta
  python -m app.accounts.cli mover-perfil ORIGEN PERFIL DESTINO [--sin-pareja]  # un perfil pasa a la cuenta de esa persona

La contraseña se pide por teclado (o en la variable BODYLENS_NEW_PASSWORD, para automatizar).
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys

from app.accounts import users
from app.core import config, db


def _password() -> str:
    pw = os.environ.get("BODYLENS_NEW_PASSWORD")
    if pw:
        return pw
    a = getpass.getpass("Contraseña: ")
    if a != getpass.getpass("Repítela: "):
        raise SystemExit("Las contraseñas no coinciden.")
    return a


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m app.accounts.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("crear-admin"); p.add_argument("usuario"); p.add_argument("nombre")
    p = sub.add_parser("crear-usuario"); p.add_argument("usuario"); p.add_argument("nombre"); p.add_argument("--correo")
    p = sub.add_parser("invitacion"); p.add_argument("nota", nargs="?", default="")
    p = sub.add_parser("contrasena"); p.add_argument("usuario")
    sub.add_parser("usuarios")
    p = sub.add_parser("fuentes"); p.add_argument("usuario"); p.add_argument("--hoja"); p.add_argument("--apps-script")
    p = sub.add_parser("mover-perfil"); p.add_argument("origen"); p.add_argument("perfil"); p.add_argument("destino")
    p.add_argument("--sin-pareja", action="store_true", help="no unir las dos cuentas en pareja")
    a = ap.parse_args(argv)
    db.init_db()
    try:
        with db.tx() as con:
            if a.cmd == "crear-admin":
                u = users.create_user(con, a.usuario, a.nombre, _password(), is_admin=True)
                print(f"Cuenta de administración «{u.username}» creada.")
            elif a.cmd == "crear-usuario":
                import secrets
                temp = os.environ.get("BODYLENS_NEW_PASSWORD") or secrets.token_urlsafe(6)
                u = users.create_user(con, a.usuario, a.nombre, temp, email=a.correo, must_change=True)
                print(f"Cuenta «{u.username}» creada. Contraseña provisional (se cambia al entrar): {temp}")
            elif a.cmd == "invitacion":
                code = users.create_invite(con, None, a.nota)
                base = config.settings.public_url or "https://<tu-dominio>"
                print(f"{base}/registro?c={code}\n(vale para una cuenta y caduca en {config.settings.invite_days} días)")
            elif a.cmd == "contrasena":
                u = users.get_by_username(con, a.usuario) or sys.exit(f"No existe «{a.usuario}».")
                users.set_password(con, u.id, _password())
                print("Contraseña cambiada; se han cerrado sus sesiones.")
            elif a.cmd == "usuarios":
                for u in users.list_users(con):
                    print(f"{u.id:>3}  {u.username:<20} {u.name:<28} {'admin' if u.is_admin else ''}"
                          f"{'  pareja=' + str(u.partner_id) if u.partner_id else ''}{'  hoja' if u.sheet_id else ''}")
            elif a.cmd == "fuentes":
                u = users.get_by_username(con, a.usuario) or sys.exit(f"No existe «{a.usuario}».")
                users.update_bridge(con, u.id, a.hoja if a.hoja is not None else u.sheet_id,
                                    a.apps_script if a.apps_script is not None else u.apps_script_url)
                print("Fuentes guardadas.")
            elif a.cmd == "mover-perfil":
                from app.data import profiles
                try:
                    r = profiles.move_profile_by_names(con, a.origen, a.perfil, a.destino, not a.sin_pareja)
                except profiles.ProfileError as e:
                    raise SystemExit(str(e))
                print(f"Movidos {r['documents']} documentos." + (" Cuentas unidas en pareja." if r["linked"] else ""))
    except users.UserError as e:
        raise SystemExit(str(e))
    finally:
        db.fix_ownership()


if __name__ == "__main__":
    main(sys.argv[1:])
