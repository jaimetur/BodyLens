"""Deleting an account with all its data: from Administration, or by the person from "Your account"."""
from __future__ import annotations

import sqlite3

from app.accounts import users
from app.accounts.users import User
from app.data import docstore
from app.sync import workbook


def delete_account(con: sqlite3.Connection, x: User) -> None:
    """Deletes the account and all its data, and cancels its subscription. A partner keeps their own copy (the couple is unlinked first); the last
    active administrator cannot be deleted (UserError)."""
    if x.is_admin and x.active:
        users.ensure_other_admin(con, x.id)
    from app.billing.routes import cancel_for   # here: billing imports the accounts module
    cancel_for(con, x.id)
    if x.partner_id:
        docstore.unlink_partner(con, x)
    con.execute("DELETE FROM invites WHERE used_by=?", (x.id,))
    con.execute("UPDATE invites SET created_by=NULL WHERE created_by=?", (x.id,))
    con.execute("DELETE FROM users WHERE id=?", (x.id,))


def delete_files(user_id: int) -> None:
    """The account's workbook on disk (after the transaction above has been committed)."""
    try:
        p = workbook.path_for(user_id)
        if p.exists():
            p.unlink()
    except OSError:
        pass
