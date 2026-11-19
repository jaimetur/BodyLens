"""Versión del código que está sirviendo el servidor.

La imagen lleva su commit en BODYLENS_REVISION. En el despliegue en caliente (código montado desde la carpeta del
stack) el fichero REVISION («<commit> <fecha>») lo escribe el script de despliegue y manda sobre la imagen: así la
página sabe que el servidor ha cambiado aunque no haya imagen nueva."""
from __future__ import annotations

import os
from pathlib import Path

REVISION_FILE = Path(os.environ.get("BODYLENS_REVISION_FILE", "/app/REVISION"))
_cache: dict = {"mtime": None, "value": None}


def current() -> dict:
    try:
        st = REVISION_FILE.stat()
        if _cache["mtime"] != st.st_mtime_ns:
            parts = REVISION_FILE.read_text(encoding="utf-8").split()
            _cache.update(mtime=st.st_mtime_ns, value={"build": parts[0] if parts else "",
                                                        "deployedAt": parts[1] if len(parts) > 1 else None})
        if _cache["value"] and _cache["value"]["build"]:
            return dict(_cache["value"])
    except OSError:
        pass
    return {"build": os.environ.get("BODYLENS_REVISION", "dev"), "deployedAt": None}
