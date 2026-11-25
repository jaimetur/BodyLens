"""Administration → Business: the panel of figures and the "Test connection" buttons of its settings."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.accounts.users import User
from app.business import sources, stats
from app.core.deps import admin_user

router = APIRouter()


@router.get("/api/admin/business")
def business(period: str = "30d", refresh: bool = False, u: User = Depends(admin_user)):
    return stats.overview(period, refresh)


class TestIn(BaseModel):
    what: str


@router.post("/api/admin/business/test")
def test_connection(body: TestIn, u: User = Depends(admin_user)):
    """Asks the service with the saved settings and says whether it answers."""
    try:
        if body.what == "stripe":
            mode = sources.stripe_test()
            return {"ok": True, "message": "Stripe responde (modo real)." if mode == "live" else "Stripe responde (modo de prueba)."}
        if body.what == "play":
            sources.play_test()
            return {"ok": True, "message": "Google Play responde y la cuenta de servicio tiene acceso a la app."}
        if body.what == "reports":
            n = sources.reports_test()
            return {"ok": True, "message": f"El bucket de informes responde ({n} informes de instalaciones)."}
    except sources.Unconfigured:
        return {"ok": False, "message": "Sin configurar."}
    except Exception as e:   # noqa: BLE001 — the message is shown next to the button
        return {"ok": False, "message": str(e)[:300]}
    raise HTTPException(400, "¿Qué conexión?")
